"""Reflector — the agent critiques its own work. Used at two moments:

  reflect_on_plan()      BEFORE coding: does the plan cover every rule in the spec?
  reflect_on_failures()  AFTER testing: why did the tests fail? (root cause, no code)

Reflection is a separate LLM call so it is visible and inspectable instead of being
hidden inside one monolithic prompt.
"""

from patterns.s03_self_reflection.planner import extract_json, plan_text
from shared.llm import generate


def reflect_on_plan(spec: str, steps: list[dict]) -> dict:
    prompt = (
        f"Specification:\n{spec}\n\nYour draft plan:\n{plan_text(steps)}\n\n"
        "Critique the plan BEFORE any code is written. Go through the specification sentence by "
        "sentence and check that each rule, error case and edge case is handled by some step. "
        "List anything missing or wrong, then output a revised plan that fixes it.\n\n"
        'Respond with JSON only:\n```json\n{"is_sound": true, "issues": ["..."], "reflection_text": "...", '
        '"changes_made": false, "revised_steps": [{"step_number":1,"goal":"...","approach":"..."}]}\n```\n'
        "If the plan is already complete: is_sound=true, issues=[], changes_made=false, and copy the steps."
    )
    raw = generate(prompt, temperature=0.2)
    try:
        data = extract_json(raw)
        revised = data.get("revised_steps") or steps
        return {
            "is_sound": bool(data.get("is_sound", True)),
            "issues": data.get("issues", []),
            "reflection_text": data.get("reflection_text", ""),
            "changes_made": bool(data.get("changes_made", False)),
            "revised_steps": revised if isinstance(revised, list) and revised else steps,
        }
    except Exception:
        return {"is_sound": True, "issues": [], "reflection_text": raw, "changes_made": False,
                "revised_steps": steps}


def reflect_on_failures(spec: str, code: str, test_output: str, earlier: list[str]) -> str:
    history = ("Earlier diagnoses (do not repeat a fix that did not work):\n- " + "\n- ".join(earlier) + "\n\n") if earlier else ""
    prompt = (
        f"Specification:\n{spec}\n\nYour code:\n```python\n{code}```\n\nTest output:\n{test_output}\n\n{history}"
        "Write a short post-mortem (max 150 words):\n"
        "1. Which tests failed and what is the ROOT CAUSE (not the symptom)?\n"
        "2. Which sentence of the specification did the code overlook?\n"
        "3. A concrete fix plan as 2-4 bullets. No code."
    )
    return generate(prompt, temperature=0.3).strip()
