"""OpenTelemetry → Azure Monitor wiring for the hosted orchestrator.

Foundry Control Plane surfaces an agent's runs, traces, and logs from the
Application Insights resource connected to the agent's project. The hosting
platform injects ``APPLICATIONINSIGHTS_CONNECTION_STRING`` into the container; a
**custom code** agent must configure OpenTelemetry itself so its spans (the
orchestration phases and each sub-agent call) are exported and show up in the
portal's **Traces** view.

This module is import-safe without the optional telemetry dependency: if
``azure-monitor-opentelemetry`` (or the connection string) is missing, it logs a
notice and the agent runs without exporting — never failing the request path.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("doc_reviewer.host")

_configured = False


def configure_foundry_telemetry() -> bool:
    """Configure Azure Monitor OpenTelemetry export if possible.

    Returns ``True`` when telemetry was configured, else ``False``. Safe to call
    multiple times; only the first successful call takes effect.
    """
    global _configured
    if _configured:
        return True

    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    if not connection_string:
        logger.info(
            "APPLICATIONINSIGHTS_CONNECTION_STRING not set; skipping Foundry "
            "telemetry export (traces won't appear in Control Plane)."
        )
        return False

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
    except ImportError:
        logger.warning(
            "azure-monitor-opentelemetry not installed; skipping telemetry "
            "export. Add it to the hosted-agent requirements to enable Foundry "
            "Control Plane traces."
        )
        return False

    # Capture GenAI message content in spans so the Traces view shows prompts and
    # responses. Reviewed documents may contain sensitive content — disable via
    # OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=false if undesired.
    os.environ.setdefault(
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true"
    )

    configure_azure_monitor(
        connection_string=connection_string,
        logger_name="doc_reviewer",
    )
    _configured = True
    logger.info("Foundry telemetry configured: exporting OpenTelemetry to Application Insights.")
    return True


def get_tracer():
    """Return an OpenTelemetry tracer, or ``None`` if OTel is unavailable."""
    try:
        from opentelemetry import trace
    except ImportError:
        return None
    return trace.get_tracer("doc_reviewer.host")


def flush_telemetry() -> None:
    """Force-export buffered spans/logs/metrics.

    Hosted agents scale to zero and the sandbox is frozen right after the
    response is returned, so the ``BatchSpanProcessor`` would otherwise never
    flush its buffer and traces would not reach Application Insights. Call this
    at the end of each request to push telemetry out before the container idles.
    """
    if not _configured:
        return
    try:
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        flush = getattr(provider, "force_flush", None)
        if flush is not None:
            flush()
    except Exception:  # noqa: BLE001 - never fail the request on a flush error
        pass

    # Flush exported logs too, if a LoggerProvider is configured.
    try:
        from opentelemetry._logs import get_logger_provider

        lp = get_logger_provider()
        lflush = getattr(lp, "force_flush", None)
        if lflush is not None:
            lflush()
    except Exception:  # noqa: BLE001
        pass
