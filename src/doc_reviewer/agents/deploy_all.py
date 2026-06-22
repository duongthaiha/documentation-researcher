"""Deploy all documentation-reviewer agents to Azure AI Foundry as prompt agents.

Iterates the per-agent packages and calls each package's ``deploy.deploy``.
Defaults to a dry run; pass ``--publish`` to actually create/version the agents.

Requires the optional ``deploy`` dependencies::

    pip install "doc-reviewer[deploy]"

Usage::

    python -m doc_reviewer.agents.deploy_all            # dry run (prints actions)
    python -m doc_reviewer.agents.deploy_all --publish  # actually publish
"""

from __future__ import annotations

import argparse
import importlib
import sys

from doc_reviewer.agents.registry import AGENT_PACKAGES
from doc_reviewer.config import Settings


def deploy_all(settings: Settings, *, dry_run: bool = True) -> None:
    """Deploy every agent package's prompt agent."""
    for package in AGENT_PACKAGES:
        deploy_module = importlib.import_module(f"{package}.deploy")
        print(f"\n=== {package} ===")
        deploy_module.deploy(settings, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="doc-reviewer-deploy",
        description="Deploy all documentation-reviewer prompt agents to Foundry.",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Actually publish (default is a dry run).",
    )
    args = parser.parse_args()

    try:
        settings = Settings.from_env()
    except ValueError as exc:
        print(f"❌ Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    deploy_all(settings, dry_run=not args.publish)


if __name__ == "__main__":
    main()
