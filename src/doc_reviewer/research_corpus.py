"""Local Markdown research corpus loading and relevance selection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


MAX_SNIPPETS = 5
MAX_SNIPPET_CHARS = 1600

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9-]{2,}", re.IGNORECASE)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "any",
    "are",
    "ask",
    "best",
    "can",
    "for",
    "from",
    "has",
    "how",
    "into",
    "its",
    "not",
    "the",
    "this",
    "using",
    "what",
    "when",
    "where",
    "which",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True)
class ResearchSnippet:
    """A relevant excerpt from a local Markdown research document."""

    source_path: str
    heading: str | None
    excerpt: str
    score: int


def find_relevant_research(
    research_dir: Path,
    query: str,
    *,
    max_snippets: int = MAX_SNIPPETS,
    max_chars_per_snippet: int = MAX_SNIPPET_CHARS,
) -> list[ResearchSnippet]:
    """Find Markdown snippets in ``research_dir`` that are relevant to ``query``."""

    if not research_dir.exists() or not research_dir.is_dir():
        return []

    keywords = _extract_keywords(query)
    if not keywords:
        return []

    snippets: list[ResearchSnippet] = []
    for path in sorted(research_dir.rglob("*.md")):
        if not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8", errors="replace")

        relative_path = _format_source_path(research_dir, path)
        for heading, section_text in _iter_markdown_sections(content):
            score = _score_text(section_text, keywords)
            if score <= 0:
                continue

            snippets.append(
                ResearchSnippet(
                    source_path=relative_path,
                    heading=heading,
                    excerpt=_make_excerpt(
                        section_text,
                        keywords,
                        max_chars=max_chars_per_snippet,
                    ),
                    score=score,
                )
            )

    snippets.sort(key=lambda snippet: (-snippet.score, snippet.source_path))
    return snippets[:max_snippets]


def format_research_context(snippets: list[ResearchSnippet]) -> str:
    """Format research snippets for injection into an agent prompt."""

    if not snippets:
        return ""

    parts = ["## Local Research Context"]
    for index, snippet in enumerate(snippets, start=1):
        title = snippet.heading or "Untitled section"
        parts.append(
            f"### Source {index}: {snippet.source_path}"
            f"{f' - {title}' if title else ''}\n\n"
            f"{snippet.excerpt}"
        )

    return "\n\n".join(parts)


def _extract_keywords(text: str) -> set[str]:
    return {
        word.lower()
        for word in _WORD_RE.findall(text)
        if word.lower() not in _STOP_WORDS
    }


def _iter_markdown_sections(content: str) -> list[tuple[str | None, str]]:
    matches = list(_HEADING_RE.finditer(content))
    if not matches:
        return [(None, content.strip())] if content.strip() else []

    sections: list[tuple[str | None, str]] = []
    if matches[0].start() > 0:
        preface = content[: matches[0].start()].strip()
        if preface:
            sections.append((None, preface))

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        heading = match.group(2).strip()
        section_text = content[start:end].strip()
        if section_text:
            sections.append((heading, section_text))

    return sections


def _score_text(text: str, keywords: set[str]) -> int:
    normalized = text.lower()
    return sum(normalized.count(keyword) for keyword in keywords)


def _make_excerpt(
    text: str,
    keywords: set[str],
    *,
    max_chars: int,
) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(compact) <= max_chars:
        return compact

    normalized = compact.lower()
    first_match = min(
        (normalized.find(keyword) for keyword in keywords if keyword in normalized),
        default=0,
    )
    start = max(0, first_match - max_chars // 3)
    end = min(len(compact), start + max_chars)
    start = max(0, end - max_chars)

    excerpt = compact[start:end].strip()
    if start > 0:
        excerpt = f"...{excerpt}"
    if end < len(compact):
        excerpt = f"{excerpt}..."
    return excerpt


def _format_source_path(research_dir: Path, path: Path) -> str:
    try:
        return str(path.relative_to(research_dir.parent))
    except ValueError:
        return str(path)
