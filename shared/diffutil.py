import difflib


def unified_diff(old: dict[str, str], new: dict[str, str]) -> str:
    """Unified diff across all files that changed (for showing agent edits)."""
    chunks = []
    for name in sorted(set(old) | set(new)):
        a, b = old.get(name, ""), new.get(name, "")
        if a != b:
            chunks.extend(difflib.unified_diff(
                a.splitlines(), b.splitlines(),
                fromfile=f"a/{name}", tofile=f"b/{name}", lineterm="",
            ))
    return "\n".join(chunks)
