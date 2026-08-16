"""Unit tests for Phase 4.3: Celery task routing, priorities, and the DLQ."""

import json

import pytest

from celery_app import celery_app
from tasks.dead_letter import (
    DEAD_LETTER_QUEUE,
    count_dead_letters,
    list_dead_letters,
    publish_dead_letter,
    requeue_dead_letters,
)


class FakeRedis:
    """Minimal in-memory stand-in for the DLQ Redis client."""

    def __init__(self):
        self.store = []

    def lpush(self, key, value):
        if key == DEAD_LETTER_QUEUE:
            self.store.insert(0, value)
        return len(self.store)

    def rpop(self, key):
        if key == DEAD_LETTER_QUEUE and self.store:
            return self.store.pop()
        return None

    def lrange(self, key, start, end):
        if key == DEAD_LETTER_QUEUE:
            stop = None if end < 0 else end + 1
            return self.store[start:stop]
        return []

    def llen(self, key):
        return len(self.store) if key == DEAD_LETTER_QUEUE else 0


@pytest.fixture
def fake_redis(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(
        "tasks.dead_letter.get_redis_client", lambda: client
    )
    return client


class TestTaskRouting:
    def test_email_tasks_route_to_high_priority_queue(self):
        routed = celery_app.amqp.router.route(
            {}, name="tasks.email_tasks.send_verification_otp_task"
        )
        assert routed["queue"].name == "email"
        # Redis: lower number = higher priority. Email must outrank retrain.
        assert routed["priority"] <= 3

    def test_email_task_glob_covers_all_email_tasks(self):
        routed = celery_app.amqp.router.route(
            {}, name="tasks.email_tasks.send_generic_email_task"
        )
        assert routed["queue"].name == "email"

    def test_retrain_routes_to_low_priority_queue(self):
        routed = celery_app.amqp.router.route(
            {}, name="tasks.ml_tasks.retrain_ranking_model"
        )
        assert routed["queue"].name == "retrain"
        assert routed["priority"] >= 9

    def test_bulk_screen_routes_to_its_queue(self):
        routed = celery_app.amqp.router.route(
            {}, name="tasks.bulk_screen_tasks.process_bulk_screen_job"
        )
        assert routed["queue"].name == "bulk_screen"

    def test_unmapped_tasks_fall_back_to_default_queue(self):
        routed = celery_app.amqp.router.route(
            {}, name="tasks.reminder_tasks.send_due_reminders"
        )
        assert routed["queue"].name == celery_app.conf.task_default_queue == "celery"
        assert celery_app.conf.task_default_priority == 5

    def test_priority_strategy_and_acks_configured(self):
        assert celery_app.conf.queue_order_strategy == "priority"
        assert celery_app.conf.task_queue_max_priority == 10
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True


class TestDeadLetterQueue:
    def test_publish_list_count(self, fake_redis):
        published = publish_dead_letter(
            celery_app,
            "tasks.email_tasks.send_generic_email_task",
            "abc-123",
            ["x@y.z"],
            {"subject": "Hi"},
            ValueError("boom"),
        )
        assert published is True
        assert count_dead_letters() == 1

        entries = list_dead_letters()
        assert len(entries) == 1
        assert entries[0]["task"] == "tasks.email_tasks.send_generic_email_task"
        assert entries[0]["task_id"] == "abc-123"
        assert entries[0]["error"] == "boom"
        assert entries[0]["args"] == ["x@y.z"]
        assert entries[0]["kwargs"] == {"subject": "Hi"}
        assert "failed_at" in entries[0]

    def test_requeue_reenqueues_via_send_task(self, fake_redis, monkeypatch):
        publish_dead_letter(
            celery_app,
            "tasks.email_tasks.send_generic_email_task",
            "t1",
            ["x@y.z"],
            {"subject": "Hi"},
            RuntimeError("nope"),
        )
        sent = []
        monkeypatch.setattr(
            celery_app, "send_task", lambda name, **kw: sent.append((name, kw))
        )

        result = requeue_dead_letters(celery_app, limit=10)
        assert result["requeued"] == 1
        assert result["remaining"] == 0
        assert count_dead_letters() == 0
        assert sent[0][0] == "tasks.email_tasks.send_generic_email_task"
        assert sent[0][1]["args"] == ["x@y.z"]
        assert sent[0][1]["task_id"] == "t1"

    def test_requeue_bad_payload_is_returned_to_dlq(self, fake_redis, monkeypatch):
        fake_redis.store.append("not-json{{{")
        sent = []
        monkeypatch.setattr(
            celery_app, "send_task", lambda name, **kw: sent.append((name, kw))
        )
        result = requeue_dead_letters(celery_app, limit=10)
        assert result["requeued"] == 0
        assert result["remaining"] == 1  # bad record preserved

    def test_on_failure_publishes_dead_letter(self, fake_redis):
        @celery_app.task(name="tasks.test_celery.always_fails")
        def always_fails():
            raise RuntimeError("kaboom")

        class FakeEinfo:
            traceback = "Traceback (most recent call last):\\n  File \"x.py\" ..."

        # Drive the base-task hook directly (avoids the eager backend, which
        # would try to reach Redis): a permanently failed task must land a
        # record in the DLQ.
        always_fails.on_failure(
            RuntimeError("kaboom"), "task-123", (), {}, FakeEinfo()
        )

        entries = list_dead_letters()
        assert len(entries) == 1
        assert entries[0]["task"] == "tasks.test_celery.always_fails"
        assert entries[0]["task_id"] == "task-123"
        assert "kaboom" in entries[0]["error"]
        assert entries[0]["traceback"]

    def test_publish_noop_without_redis(self, monkeypatch):
        # Simulate no configured Redis (as in the unit-test environment).
        monkeypatch.setattr("tasks.dead_letter.get_redis_client", lambda: None)
        assert publish_dead_letter(
            celery_app, "tasks.x.y", "id-1", [], {}, Exception("x")
        ) is False
        assert count_dead_letters() == 0
