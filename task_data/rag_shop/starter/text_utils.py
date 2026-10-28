"""Small text helpers."""
import re


def slugify(text: str) -> str:
    """Lowercase, replace runs of non-alphanumerics with '-', trim dashes."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def truncate(text: str, width: int) -> str:
    """Shorten text to at most `width` characters, adding an ellipsis."""
    return text if len(text) <= width else text[: width - 1] + "…"
