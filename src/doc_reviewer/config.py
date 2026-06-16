"""Configuration for the documentation reviewer."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    project_endpoint: str
    model_deployment_name: str
    workiq_mcp_url: str
    review_rounds: int = 3
    ms_learn_mcp_url: str = "https://learn.microsoft.com/api/mcp"

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        project_endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
        model_deployment_name = os.environ.get(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o"
        )
        workiq_mcp_url = os.environ.get("WORKIQ_MCP_URL", "")
        review_rounds = int(os.environ.get("REVIEW_ROUNDS", "3"))

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

        return cls(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment_name,
            workiq_mcp_url=workiq_mcp_url,
            review_rounds=review_rounds,
        )
