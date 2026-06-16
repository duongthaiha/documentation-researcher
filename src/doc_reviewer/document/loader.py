"""Document loader for markdown and PDF files."""

from pathlib import Path


def load_document(file_path: str) -> str:
    """Load a document and return its text content.

    Supports markdown (.md) and PDF (.pdf) files.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".md":
        return _load_markdown(path)
    elif suffix == ".pdf":
        return _load_pdf(path)
    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. Supported: .md, .pdf"
        )


def _load_markdown(path: Path) -> str:
    """Load a markdown file as plain text."""
    return path.read_text(encoding="utf-8")


def _load_pdf(path: Path) -> str:
    """Extract text from a PDF file using pymupdf."""
    import pymupdf

    text_parts: list[str] = []
    with pymupdf.open(str(path)) as doc:
        for page in doc:
            text_parts.append(page.get_text())

    return "\n".join(text_parts)
