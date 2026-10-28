"""Task loader — every demo task is a folder under task_data/.

task_data/<key>/
    task.json        title, kind, entry file, one-line summary
    spec.md          the natural-language requirement / bug report shown to agents
    starter/         files the agent starts with (empty for greenfield tasks)
    test_suite.py    the executable ground truth (unittest)
    probes.txt       optional: one Python expression per line, for behavioural voting
    reference/       a known-good solution (used ONLY by tests/, never shown to agents)
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "task_data"


@dataclass
class Task:
    key: str
    title: str
    kind: str                       # generate | fix | feature | review | refactor
    summary: str
    spec: str
    entry: str                      # main file the agent edits/creates
    starter: dict[str, str]         # files visible to the agent at the start
    tests: str                      # contents of test_suite.py
    probes: list[str] = field(default_factory=list)
    vague_goal: str = ""            # terse user request (Proactive Goal Creator demo)


def _read_dir(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        str(p.relative_to(path)): p.read_text()
        for p in sorted(path.rglob("*.py"))
        if "__pycache__" not in p.parts
    }


def load_task(key: str) -> Task:
    folder = DATA_DIR / key
    meta = json.loads((folder / "task.json").read_text())
    probes_file = folder / "probes.txt"
    probes = [l for l in probes_file.read_text().splitlines() if l.strip()] if probes_file.exists() else []
    return Task(
        key=key,
        title=meta["title"],
        kind=meta["kind"],
        summary=meta["summary"],
        spec=(folder / "spec.md").read_text().strip(),
        entry=meta.get("entry", "solution.py"),
        starter=_read_dir(folder / "starter"),
        tests=(folder / "test_suite.py").read_text(),
        probes=probes,
        vague_goal=meta.get("vague_goal", ""),
    )


def load_reference(key: str) -> dict[str, str]:
    """Known-good files for a task — for the project's own tests only."""
    return _read_dir(DATA_DIR / key / "reference")


def list_tasks() -> list[str]:
    return sorted(p.name for p in DATA_DIR.iterdir() if (p / "task.json").exists())
