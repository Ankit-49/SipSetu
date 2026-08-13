"""OpenTelemetry distributed tracing (Phase 3.3, optional).

Enabled only when ``OTEL_ENABLED`` is truthy AND the opentelemetry packages
are installed; otherwise ``setup_tracing`` is a safe no-op so the app runs
unchanged without the extra dependencies.

Configuration (environment variables):

- ``OTEL_ENABLED`` (default ``false``) — master switch.
- ``OTEL_SERVICE_NAME`` (default ``sipsetu``) — resource ``service.name``.
- ``OTEL_EXPORTER_OTLP_ENDPOINT`` (default ``http://localhost:4317``) —
  OTLP/gRPC endpoint. In docker-compose the backend is pointed at the
  bundled ``otel-collector`` service.
- ``OTEL_TRACES_SAMPLE_RATE`` (default ``0.1``) — ratio of root spans that
  produce traces (10% traces, matching the roadmap target; child spans of a
  sampled parent are always kept via ``ParentBased``).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def setup_tracing(app) -> bool:
    """Instrument the Flask app (and SQLAlchemy/requests) with OpenTelemetry.

    Returns True when tracing was enabled, False when it was skipped
    (disabled by config, or packages not installed).
    """
    if os.environ.get("OTEL_ENABLED", "").lower() not in ("1", "true", "yes"):
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
    except ImportError as e:
        app.logger.warning(f"OpenTelemetry packages not installed; tracing disabled: {e}")
        return False

    service_name = os.environ.get("OTEL_SERVICE_NAME", "sipsetu")
    sample_rate = float(os.environ.get("OTEL_TRACES_SAMPLE_RATE", "0.1"))

    try:
        provider = TracerProvider(
            resource=Resource.create({"service.name": service_name}),
            sampler=ParentBased(TraceIdRatioBased(min(max(sample_rate, 0.0), 1.0))),
        )
        # The exporter reads OTEL_EXPORTER_OTLP_ENDPOINT from the environment.
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)

        FlaskInstrumentor().instrument_app(app)
        SQLAlchemyInstrumentor().instrument()
        RequestsInstrumentor().instrument()

        app.logger.info(
            "OpenTelemetry tracing enabled "
            f"(service={service_name}, sample_rate={sample_rate})"
        )
        return True
    except Exception as e:  # pragma: no cover - defensive
        app.logger.warning(f"Failed to initialize OpenTelemetry tracing: {e}")
        return False
