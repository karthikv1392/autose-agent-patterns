"""Planner — drafts an implementation plan BEFORE any code is written."""

import json
import re

from shared.llm import generate


def extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text) or re.search(r"(\{[\s\S]*\})", text)
    return json.loads(match.group(1).strip())


def plan_text(steps: list[dict]) -> str:
    return "\n".join(f"{s.get('step_number', i)}. {s.get('goal', '')} — {s.get('approach', '')}"
                     for i, s in enumerate(steps, 1))


def create_plan(spec: str) -> list[dict]:
    prompt = (
        f"Specification:\n{spec}\n\n"
        "Draft a 3-5 step implementation plan for a Python engineer. For each step give the sub-goal "
        "and the concrete approach (data structures, parsing strategy, validation, edge cases). "
        "Prefer the simplest design that satisfies every rule, using standard-library idioms "
        "(for example one anchored regular expression) over hand-written tokenizers or state machines.\n\n"
        'Respond with JSON only:\n```json\n{"steps":[{"step_number":1,"goal":"...","approach":"..."}]}\n```'
    )
    raw = generate(prompt, temperature=0.4)
    try:
        steps = extract_json(raw).get("steps", [])
        if steps:
            return steps
    except Exception:
        pass
    return [{"step_number": 1, "goal": "Implement the specification", "approach": raw.strip()[:500]}]
