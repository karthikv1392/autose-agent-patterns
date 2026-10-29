"""Skill agent — searches the library, solves the task, and drafts the metadata for a new skill.

Two phases, as in the generic Skill Library pattern:

Phase 1, search   the agent sees short summaries of every skill (never the full code) and picks
                  the few that are worth reusing. Only those are loaded for phase 2.
Phase 2, solve    the agent writes the solution, adapting the retrieved skills when there are any,
                  and describes the result so it could be saved as a skill.
"""

import json

from shared.agent import Agent
from shared.codeutil import extract_code
from patterns.m05_skill_repository.skill_store import Skill, SkillStore

PERSONA = ("You are a senior Python engineer who keeps a growing library of reusable solutions. "
           "Before writing code you check the library for earlier solutions you can reuse. You adapt "
           "or combine them when they genuinely fit, and you describe each new solution clearly so "
           "that a future session can find it.")

AGENT = Agent("Skill Agent", PERSONA, temperature=0.2)


def _extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def search_skills(store: SkillStore, task_spec: str, top_k: int) -> dict:
    """Phase 1: pick up to `top_k` skills whose solutions could be reused for this task."""
    summaries = store.summaries_for_retrieval()
    if not summaries:
        return {"retrieved": [], "reasoning": "The library is empty, so the agent solves from scratch.",
                "searched": 0}

    listing = "\n".join(
        f'[{i + 1}] id={s["id"]}\n    Name: {s["name"]}  ({s["task_type"]})\n'
        f'    Tags: {", ".join(s["tags"])}\n    Description: {s["description"]}\n'
        f'    Original task: {s["task_solved_preview"]}'
        for i, s in enumerate(summaries))
    raw = AGENT.ask(
        f"New task:\n{task_spec}\n\nSkill library ({len(summaries)} skills):\n{listing}\n\n"
        f"Choose up to {top_k} skills whose solutions could be REUSED, ADAPTED or COMBINED for the new "
        "task. Only pick a skill with a real overlap; a shared broad topic is not enough. Choosing "
        "none is fine.\n\nReturn ONLY JSON:\n"
        '{"relevant_skill_ids": ["<id>"], "reasoning": "<2-3 sentences>"}')
    data = _extract_json(raw)
    retrieved = []
    for skill_id in data.get("relevant_skill_ids", [])[:top_k]:
        skill = store.get(str(skill_id))
        if skill:
            retrieved.append(skill)
            store.increment_use(skill.id)
    return {"retrieved": retrieved, "reasoning": str(data.get("reasoning", "")), "searched": len(summaries)}


def solve(task_spec: str, entry: str, retrieved: list[Skill]) -> dict:
    """Phase 2: write the solution and the metadata for saving it."""
    if retrieved:
        skills = "\n\n".join(f"=== Retrieved skill: {s.name} ===\nDescription: {s.description}\n"
                             f"Solution:\n```python\n{s.solution}\n```" for s in retrieved)
        guidance = ("Build on the retrieved skills: adapt, extend or combine them, and check them against "
                    "the specification. Do not copy a skill that does not fit.")
        default_approach = "adapted_from_skill" if len(retrieved) == 1 else "combined_skills"
    else:
        skills, guidance, default_approach = "(none)", "No relevant skill was found. Solve from scratch.", "from_scratch"

    raw = AGENT.ask(
        f"Task:\n{task_spec}\n\nRetrieved skills:\n{skills}\n\n{guidance}\n\n"
        "Reply with two fenced blocks. First a ```json block with the metadata of the new skill:\n"
        f'{{"approach": "{default_approach}", "skills_used": ["<skill name>"], "is_reusable": true, '
        '"name": "<5 words or fewer>", "description": "<one sentence>", "tags": ["<tag>", "<tag>"]}\n'
        "Set is_reusable to false only if the solution is too specific to this task to help with another.\n"
        f"Then a ```python block with the COMPLETE `{entry}` and nothing else.")
    meta = _extract_json(raw.split("```python")[0])
    code = extract_code(raw)
    return {
        "code": code,
        "approach": str(meta.get("approach", default_approach)),
        "skills_used": [str(x) for x in meta.get("skills_used", [])],
        "is_reusable": bool(meta.get("is_reusable", True)),
        "name": str(meta.get("name", "")).strip() or "Unnamed skill",
        "description": str(meta.get("description", "")).strip() or f"Solution for: {task_spec[:80]}",
        "tags": [str(t) for t in meta.get("tags", [])][:6],
    }
