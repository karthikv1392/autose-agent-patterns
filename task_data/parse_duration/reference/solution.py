import re

_PATTERN = re.compile(
    r"(?:(\d+)\s*d)?\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?",
    re.IGNORECASE | re.ASCII,
)


def parse_duration(text: str) -> int:
    s = text.strip()
    if not s:
        raise ValueError("empty duration")
    if re.fullmatch(r"\d+", s, re.ASCII):
        return int(s)
    m = _PATTERN.fullmatch(s)
    if not m or all(g is None for g in m.groups()):
        raise ValueError(f"invalid duration: {text!r}")
    d, h, mi, sec = (int(g) if g else 0 for g in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + sec
