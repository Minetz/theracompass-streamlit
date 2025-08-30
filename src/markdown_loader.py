"""Utility to load markdown content for Streamlit pages."""

from pathlib import Path

MARKDOWN_DIR = Path(__file__).parent / "markdown"


def load_markdown(filename: str) -> str:
    """Return the contents of a markdown file from the markdown directory."""
    return (MARKDOWN_DIR / filename).read_text(encoding="utf-8")
