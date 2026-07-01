"""Optional Langfuse observability setup."""

import logging
import os

from doc_reviewer.config import Settings

# Third-party loggers that can flood the console (Langfuse and its HTTP/OTel
# dependencies). Their level is capped to the configured log level.
_NOISY_LOGGERS = (
    "langfuse",
    "httpx",
    "httpcore",
    "openai",
    "opentelemetry",
    "azure",
    "azure.core.pipeline.policies.http_logging_policy",
)


def configure_logging(level: str) -> None:
    """Configure console logging verbosity for the app and noisy libraries.

    Set ``level`` to ``WARNING`` (or higher) to hide informational Langfuse and
    HTTP client logs from the console.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
    logging.getLogger().setLevel(numeric_level)
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(numeric_level)


def configure_observability(settings: Settings) -> None:
    """Configure Langfuse/OpenTelemetry observability when enabled."""
    if not settings.langfuse_enabled:
        print("🔭 Langfuse observability: disabled")
        return

    _apply_langfuse_environment(settings)

    try:
        from agent_framework.observability import configure_otel_providers
        from langfuse import get_client
    except ImportError as exc:
        raise RuntimeError(
            "Langfuse observability is enabled but required packages are missing. "
            "Run `pip install -r requirements.txt`."
        ) from exc

    langfuse = get_client()
    if not langfuse.auth_check():
        raise RuntimeError(
            "Langfuse authentication failed. Check LANGFUSE_PUBLIC_KEY, "
            "LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL."
        )

    configure_otel_providers(
        enable_sensitive_data=settings.langfuse_enable_sensitive_data
    )
    print(f"🔭 Langfuse observability: enabled ({settings.langfuse_base_url})")


def flush_observability(settings: Settings) -> None:
    """Flush Langfuse telemetry for short-lived CLI runs."""
    if not settings.langfuse_enabled:
        return

    try:
        from langfuse import get_client
    except ImportError:
        return

    get_client().flush()


def _apply_langfuse_environment(settings: Settings) -> None:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    os.environ["LANGFUSE_BASE_URL"] = settings.langfuse_base_url
    os.environ["LANGFUSE_DEBUG"] = str(settings.langfuse_debug)
