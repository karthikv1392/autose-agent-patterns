"""Trace — a uniform, UI-agnostic log of what an agent did.

Every pattern's `run()` writes human-readable events to a Trace. The Streamlit
app renders them live; the CLI prints them. This keeps the pattern code free of
UI concerns, so students can read each agent.py in isolation.

NOTE: call `add()` from the main thread only (patterns that use thread pools
collect results first, then log), because Streamlit rendering is not thread-safe.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

# Event kinds the renderers understand:
#   step   — a section heading ("Attempt 2")
#   text   — markdown prose (agent reasoning, critiques)
#   code   — source code (lang field)
#   tests  — test-runner output; `ok` says whether the run was green
#   table  — `data` is a list of row dicts
#   result — the final outcome banner; `ok` says success


@dataclass
class Event:
    kind: str
    title: str
    body: str = ""
    lang: str | None = None
    ok: bool | None = None
    agent: str | None = None
    data: Any = None


@dataclass
class Trace:
    on_event: Callable[[Event], None] | None = None
    events: list[Event] = field(default_factory=list)

    def add(self, title: str, body: str = "", kind: str = "text", **kw) -> None:
        event = Event(kind=kind, title=title, body=body, **kw)
        self.events.append(event)
        if self.on_event:
            self.on_event(event)


def print_event(e: Event) -> None:
    """CLI renderer used by `python -m patterns.<name>.agent`."""
    bar = "=" * 70
    if e.kind == "step":
        print(f"\n{bar}\n{e.title}\n{bar}")
        return
    who = f"[{e.agent}] " if e.agent else ""
    flag = {True: " ✅", False: " ❌", None: ""}[e.ok]
    print(f"\n--- {who}{e.title}{flag}")
    if e.kind == "table":
        for row in e.data or []:
            print("   ", row)
    elif e.body:
        print(e.body)
