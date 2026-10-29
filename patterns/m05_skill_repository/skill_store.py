"""Skill store — a persistent library of reusable solutions, backed by a JSON file.

A skill is a solution that worked once, saved with enough metadata (name, description,
tags, the task it solved) for a later session to find it again. The library starts from
`skill_library.seed.json` and then grows in `skill_library.json` (ignored by git), so a
demo run never edits the tracked seed. Delete `skill_library.json` to start over.
"""

import json
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
SEED_PATH = HERE / "skill_library.seed.json"
LIBRARY_PATH = HERE / "skill_library.json"


@dataclass
class Skill:
    id: str
    name: str
    description: str
    task_type: str            # Code | Analysis | Planning | Writing | General
    tags: list[str]
    task_solved: str          # the task that produced this skill
    solution: str             # the reusable output (source code here)
    created_at: str           # ISO 8601
    use_count: int = 0        # times a later session retrieved it
    author: str = "SkillAgent"


def make_skill(name: str, description: str, tags: list[str], task_solved: str, solution: str,
               task_type: str = "Code") -> Skill:
    return Skill(id=str(uuid.uuid4()), name=name, description=description, task_type=task_type,
                 tags=tags, task_solved=task_solved, solution=solution,
                 created_at=datetime.now(timezone.utc).isoformat())


class SkillStore:
    """JSON-backed library. Single-user and synchronous, which is fine for a classroom demo."""

    def __init__(self, path: Path = LIBRARY_PATH, seed: Path = SEED_PATH):
        self.path = path
        if not path.exists() and seed.exists():
            shutil.copy(seed, path)
        self._skills: dict[str, Skill] = {}
        try:
            for item in json.loads(path.read_text()).get("skills", []):
                skill = Skill(**item)
                self._skills[skill.id] = skill
        except (OSError, json.JSONDecodeError, TypeError):
            pass                                   # missing or corrupt file: start empty

    def _persist(self) -> None:
        self.path.write_text(json.dumps({"skills": [asdict(s) for s in self._skills.values()]}, indent=2))

    def add(self, skill: Skill) -> Skill:
        self._skills[skill.id] = skill
        self._persist()
        return skill

    def increment_use(self, skill_id: str) -> None:
        if skill_id in self._skills:
            self._skills[skill_id].use_count += 1
            self._persist()

    def get(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def all_skills(self) -> list[Skill]:
        return sorted(self._skills.values(), key=lambda s: s.created_at, reverse=True)

    def size(self) -> int:
        return len(self._skills)

    def summaries_for_retrieval(self) -> list[dict]:
        """Short descriptions only. Full solutions are loaded for the skills that get selected,
        so the retrieval prompt stays small however large the library grows."""
        return [{"id": s.id, "name": s.name, "description": s.description, "task_type": s.task_type,
                 "tags": s.tags, "task_solved_preview": s.task_solved[:180]} for s in self.all_skills()]
