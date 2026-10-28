"""Small helpers for pulling code and sections out of LLM responses."""

import re

_FENCE = re.compile(r"```[ \t]*([\w+-]*)[ \t]*\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """Return the Python source from an LLM response.

    Prefers the longest ```python fenced block; falls back to any fenced block,
    then to the raw text. Small models sometimes forget the fence, so we are lenient.
    """
    blocks = _FENCE.findall(text)
    python_blocks = [code for lang, code in blocks if lang.lower() in ("python", "py")]
    pool = python_blocks or [code for _, code in blocks]
    if pool:
        return max(pool, key=len).strip("\n") + "\n"
    return text.strip("\n") + "\n"


def extract_sections(text: str) -> dict[str, str]:
    """Split a markdown response on `## Heading` lines -> {lowercase heading: body}."""
    sections: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^#{2,3}\s+(.*?)\s*$", line)
        if m:
            current = m.group(1).strip().lower()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return {k: v.strip() for k, v in sections.items()}


def truncate(text: str, limit: int = 2500) -> str:
    """Keep prompts and observations bounded."""
    if len(text) <= limit:
        return text
    return text[: limit // 2] + "\n... [truncated] ...\n" + text[-limit // 2 :]


_FILE_BLOCK = re.compile(
    r"#+\s*(?:FILE:\s*)?`?([\w./-]+\.py)`?[ \t]*\n+```[\w]*[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE
)


def extract_files(text: str) -> dict[str, str]:
    """Parse a multi-file reply: `### FILE: name.py` followed by a fenced code block."""
    return {name: code.strip("\n") + "\n" for name, code in _FILE_BLOCK.findall(text)}
