"""Business metrics (Prometheus counters) for SipSetu.

Counters are created lazily and registered against the app's Prometheus
registry, then cached on the app instance. If metrics are disabled the
helpers become no-ops, so endpoints can call them unconditionally.
"""

from __future__ import annotations

from typing import Any


def _registry(app):
    metrics = getattr(app, "metrics", None)
    if metrics is None:
        return None
    return getattr(metrics, "registry", None)


def increment(app, name: str, description: str, labels: dict | None = None):
    registry = _registry(app)
    if registry is None:
        return

    from prometheus_client import Counter

    labels = labels or {}
    counters = getattr(app, "_metrics_counters", None)
    if counters is None:
        counters = {}
        app._metrics_counters = counters

    counter: Any = counters.get(name)
    if counter is None:
        counter = Counter(
            name, description, labelnames=list(labels.keys()), registry=registry
        )
        counters[name] = counter

    if labels:
        counter.labels(**labels).inc()
    else:
        counter.inc()


def gauge_set(app, name: str, description: str, value: float, labels: dict | None = None):
    """Set a Prometheus gauge (lazily created against the app registry).

    Useful for reporting instantaneous state such as DB pool utilization or
    dependency up/down status. Callers are expected to refresh the value on
    a cadence (e.g. inside the health-check endpoint); if metrics are
    disabled this is a no-op.
    """
    registry = _registry(app)
    if registry is None:
        return

    from prometheus_client import Gauge

    labels = labels or {}
    gauges = getattr(app, "_metrics_gauges", None)
    if gauges is None:
        gauges = {}
        app._metrics_gauges = gauges

    key = (name, tuple(sorted(labels.items())))
    gauge: Any = gauges.get(key)
    if gauge is None:
        gauge = Gauge(
            name, description, labelnames=list(labels.keys()), registry=registry
        )
        gauges[key] = gauge

    if labels:
        gauge.labels(**labels).set(value)
    else:
        gauge.set(value)
