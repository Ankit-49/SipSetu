"""Integration tests for GET /jobs?search=.

On Postgres the search path is full-text (``search_vector @@ plainto_tsquery``,
migration 005) with relevance ranking; on SQLite — which is what the test
suite runs against — it falls back to the leading-wildcard ILIKE over
title/location/job_type. These tests pin the fallback behavior so the
full-text switch never silently breaks SQLite/dev search.
"""


class TestJobSearch:
    def test_search_matches_title(self, client, test_job):
        response = client.get("/api/v1/jobs?search=engineer")
        assert response.status_code == 200
        titles = [j["title"] for j in response.get_json()["data"]]
        assert "Software Engineer" in titles

    def test_search_matches_location_and_job_type(self, client, test_job):
        # The fallback ILIKE covers title/location/job_type (not description).
        for term in ("remote", "full-time"):
            response = client.get(f"/api/v1/jobs?search={term}")
            assert response.status_code == 200
            titles = [j["title"] for j in response.get_json()["data"]]
            assert "Software Engineer" in titles

    def test_search_no_match(self, client, test_job):
        response = client.get("/api/v1/jobs?search=zzzznotpresent")
        assert response.status_code == 200
        assert response.get_json()["data"] == []

    def test_search_short_term_fallback(self, client, test_job):
        # 1-2 char terms never take the full-text path (needs >= 3 chars), so
        # this exercises the ILIKE fallback on any dialect.
        response = client.get("/api/v1/jobs?search=en")
        assert response.status_code == 200
        titles = [j["title"] for j in response.get_json()["data"]]
        assert "Software Engineer" in titles

    def test_search_legacy_prefix(self, client, test_job):
        response = client.get("/api/jobs?search=engineer")
        assert response.status_code == 200
        titles = [j["title"] for j in response.get_json()["jobs"]]
        assert "Software Engineer" in titles
