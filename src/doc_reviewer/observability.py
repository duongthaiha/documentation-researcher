"""Optional Langfuse observability setup."""

import os

from doc_reviewer.config import Settings


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
