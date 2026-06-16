"""CLI entry point for the documentation reviewer."""

import argparse
import asyncio
import sys
from pathlib import Path

from doc_reviewer.config import Settings
from doc_reviewer.document.loader import load_document
from doc_reviewer.observability import configure_observability, flush_observability
from doc_reviewer.orchestrator import run_review

SUPPORTED_INDUSTRIES = ["fsi", "manufacturing", "engineering"]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="doc-reviewer",
        description="Multi-agent documentation reviewer. Customer agents ask questions, "
        "Research agent answers, Writer agent updates the document.",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the document to review (markdown or PDF)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="Number of Q&A rounds (default: 3)",
    )
    parser.add_argument(
        "--industry",
        nargs="+",
        choices=SUPPORTED_INDUSTRIES,
        default=SUPPORTED_INDUSTRIES,
        help="Industries to include (default: all)",
    )
    parser.add_argument(
        "--research-dir",
        help="Directory of local Markdown research docs (default: ./research or RESEARCH_DIR)",
    )
    return parser.parse_args()


def _get_output_path(input_path: str) -> Path:
    """Generate output path for the reviewed document."""
    path = Path(input_path)
    return path.parent / f"{path.stem}_reviewed{path.suffix}"


async def async_main() -> None:
    """Async entry point."""
    args = parse_args()

    # Load configuration
    try:
        settings = Settings.from_env()
    except ValueError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        configure_observability(settings)
    except RuntimeError as e:
        print(f"❌ Observability error: {e}", file=sys.stderr)
        sys.exit(1)

    # Override rounds if specified
    if args.rounds:
        settings.review_rounds = args.rounds
    if args.research_dir:
        settings.research_dir = Path(args.research_dir).expanduser()

    # Load document
    try:
        document_content = load_document(args.file)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error loading document: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"📄 Loaded document: {args.file}")
    print(f"🏭 Industries: {', '.join(args.industry)}")
    print(f"🔄 Rounds: {settings.review_rounds}")
    print(f"🔎 Research directory: {settings.research_dir}")

    try:
        # Run review
        conversation, updated_document = await run_review(
            settings=settings,
            document_content=document_content,
            industries=args.industry,
            rounds=settings.review_rounds,
            research_dir=settings.research_dir,
        )

        # Save updated document
        output_path = _get_output_path(args.file)
        output_path.write_text(updated_document, encoding="utf-8")
        print(f"\n📄 Updated document saved to: {output_path}")
        print(f"💬 Total conversation turns: {len(conversation)}")
    finally:
        flush_observability(settings)


def main() -> None:
    """Synchronous entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
