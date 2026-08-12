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

    counter.labels(**labels).inc()
