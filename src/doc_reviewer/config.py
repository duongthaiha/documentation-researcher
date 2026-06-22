"""Configuration for the documentation reviewer."""

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_research_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "research"


def _get_github_token() -> str:
    """Get GitHub token from env var or fall back to gh CLI auth."""
    token = os.environ.get("GITHUB_MCP_TOKEN", "")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    project_endpoint: str
    model_deployment_name: str
    workiq_mcp_url: str
    github_mcp_token: str = ""
    research_dir: Path = field(default_factory=_default_research_dir)
    review_rounds: int = 3
    ms_learn_mcp_url: str = "https://learn.microsoft.com/api/mcp"
    github_mcp_url: str = "https://api.githubcopilot.com/mcp/"
    # Foundry connection IDs for authenticated MCP servers when agents are
    # deployed as hosted prompt agents (Foundry forbids inline auth headers).
    github_mcp_connection_id: str = ""
    workiq_mcp_connection_id: str = ""
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "http://localhost:3000"
    langfuse_enable_sensitive_data: bool = False
    langfuse_debug: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        project_endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
        model_deployment_name = os.environ.get(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o"
        )
        workiq_mcp_url = os.environ.get("WORKIQ_MCP_URL", "")
        github_mcp_token = _get_github_token()
        github_mcp_connection_id = os.environ.get("GITHUB_MCP_CONNECTION_ID", "")
        workiq_mcp_connection_id = os.environ.get("WORKIQ_MCP_CONNECTION_ID", "")
        review_rounds = int(os.environ.get("REVIEW_ROUNDS", "3"))
        research_dir = Path(
            os.environ.get(
                "RESEARCH_DIR",
                str(_default_research_dir()),
            )
        ).expanduser()
        langfuse_enabled = _get_bool_env("LANGFUSE_ENABLED", False)
        langfuse_public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        langfuse_secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
        langfuse_base_url = os.environ.get("LANGFUSE_BASE_URL", "http://localhost:3000")
        langfuse_enable_sensitive_data = _get_bool_env(
            "LANGFUSE_ENABLE_SENSITIVE_DATA", False
        )
        langfuse_debug = _get_bool_env("LANGFUSE_DEBUG", False)

        if not project_endpoint:
            raise ValueError(
                "AZURE_AI_PROJECT_ENDPOINT environment variable is required. "
                "See .env.example for configuration."
            )
        if not workiq_mcp_url:
            raise ValueError(
                "WORKIQ_MCP_URL environment variable is required. "
                "See .env.example for configuration."
            )
        if langfuse_enabled and (not langfuse_public_key or not langfuse_secret_key):
            raise ValueError(
                "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required when "
                "LANGFUSE_ENABLED=true."
            )

        return cls(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment_name,
            workiq_mcp_url=workiq_mcp_url,
            github_mcp_token=github_mcp_token,
            github_mcp_connection_id=github_mcp_connection_id,
            workiq_mcp_connection_id=workiq_mcp_connection_id,
            research_dir=research_dir,
            review_rounds=review_rounds,
            langfuse_enabled=langfuse_enabled,
            langfuse_public_key=langfuse_public_key,
            langfuse_secret_key=langfuse_secret_key,
            langfuse_base_url=langfuse_base_url,
            langfuse_enable_sensitive_data=langfuse_enable_sensitive_data,
            langfuse_debug=langfuse_debug,
        )
