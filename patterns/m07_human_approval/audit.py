"""Audit trail — an append-only record of every plan, notification, decision and execution."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class Entry:
    seq: int
    action_index: int
    action: str
    risk_level: str
    event: str                 # planned | notified | auto_approved | approved | rejected | executed | skipped
    actor: str                 # "system" or the reviewer's name
    timestamp: str
    notes: str = ""


class AuditTrail:
    def __init__(self) -> None:
        self._entries: list[Entry] = []

    def log(self, action: dict, event: str, actor: str = "system", notes: str = "") -> None:
        self._entries.append(Entry(len(self._entries) + 1, action["index"], action["action"], action["risk_level"],
                                   event, actor, datetime.now(timezone.utc).isoformat(timespec="seconds"), notes))

    def rows(self) -> list[dict]:
        return [asdict(e) for e in self._entries]

    def events(self, event: str) -> list[Entry]:
        return [e for e in self._entries if e.event == event]
