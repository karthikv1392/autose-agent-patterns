"""Critic — scores a draft against explicit criteria and decides whether it passes the gate.

The critic only READS the code; it never runs it. Its opinion is what drives the loop, which is
exactly why the demo also runs the real tests after every iteration, to show where the two disagree.

Gate: the draft passes when the overall score is at least 7 AND the must-fix list is empty.
"""

import json
import re

from shared.agent import Agent

CRITERIA = ["correctness", "security", "efficiency", "readability", "error_handling"]
PASS_SCORE = 7

PERSONA = ("You are a rigorous code reviewer with very high standards. You judge work objectively against "
           "specific criteria, give actionable feedback, and approve only work that genuinely meets a high "
           "bar. A score of 7 or more means the criterion is genuinely good, not just passable.")

CRITIC = Agent("Critic", PERSONA, temperature=0.2)


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


def critique(spec: str, draft: str, iteration: int) -> dict:
    template = ", ".join(f'"{c}": {{"score": <1-10>, "feedback": "<string>", "severity": "ok|must_fix|nice_to_have"}}'
                         for c in CRITERIA)
    raw = CRITIC.ask(
        f"You are reviewing a Python draft (iteration {iteration}).\n\nOriginal task:\n{spec}\n\n"
        f"Draft:\n```python\n{draft}```\n\n"
        f"Evaluate it against these criteria: {', '.join(CRITERIA)}. For each, give a score from 1 to 10, "
        "feedback, and a severity.\n"
        "  1-4 unacceptable (must_fix)   5-6 below par (must_fix if critical)   7-8 good (nice_to_have)   9-10 excellent (ok)\n"
        f"The draft PASSES if the overall score is at least {PASS_SCORE} and there are no must_fix issues. "
        "List one short sentence in must_fix for every criterion with severity must_fix.\n\n"
        f'Return ONLY JSON:\n{{"criteria_scores": {{{template}}}, "overall_score": <1-10>, '
        '"overall_feedback": "<2-3 sentences>", "must_fix": ["<issue>"]}')
    return _parse(_extract_json(raw))


def _parse(data: dict) -> dict:
    """Normalise whatever the model returned so the loop can rely on every field."""
    def clamp(value, default=5) -> int:
        try:
            return max(1, min(10, int(value)))
        except (TypeError, ValueError):
            return default

    scores = data.get("criteria_scores") if isinstance(data.get("criteria_scores"), dict) else {}
    rows = {}
    for c in CRITERIA:
        entry = scores.get(c) if isinstance(scores.get(c), dict) else {}
        score = clamp(entry.get("score"))
        severity = str(entry.get("severity", ""))
        if severity not in ("ok", "must_fix", "nice_to_have"):
            severity = "must_fix" if score < PASS_SCORE else "ok"
        rows[c] = {"score": score, "feedback": str(entry.get("feedback", "No feedback provided.")), "severity": severity}

    must_fix = data.get("must_fix") if isinstance(data.get("must_fix"), list) else []
    if not must_fix:                                      # the model forgot the list: rebuild it from the criteria
        must_fix = [f"{c}: {r['feedback']}" for c, r in rows.items() if r["severity"] == "must_fix"]
    overall = clamp(data.get("overall_score"))
    return {"passed": overall >= PASS_SCORE and not must_fix, "overall_score": overall, "criteria_scores": rows,
            "overall_feedback": str(data.get("overall_feedback", "Critique completed.")), "must_fix": [str(m) for m in must_fix]}
