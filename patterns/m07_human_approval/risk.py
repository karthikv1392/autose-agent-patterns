"""Risk classifier — scores each action and decides whether a human must approve it.

LOW    1-3   read-only or fully reversible, no effect outside the sandbox     runs automatically
MEDIUM 4-6   ordinary edits, reversible with a revert, limited blast radius   runs, flagged for awareness
HIGH   7-10  hard to reverse, wide blast radius, or touches shared systems     waits for a human decision

The level is derived from the score, so an inconsistent model reply cannot lower it.
"""

import json
import re

from shared.agent import Agent

PERSONA = "You are a risk assessment specialist for a software engineering team."

CLASSIFIER = Agent("Risk classifier", PERSONA, temperature=0.1)

CONTEXT = ("Reading files and running tests in the sandbox is LOW. An ordinary fix inside a function body, "
           "which a revert undoes, is MEDIUM. HIGH covers changes that callers or other systems depend on or "
           "that are hard to undo: changing a public signature or return shape, editing build, CI or "
           "dependency configuration, adding a dependency, deleting code or branches, force-pushing, "
           "changing database migrations, and anything that touches production or secrets.")


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


def level_for(score: int) -> str:
    return "low" if score <= 3 else "medium" if score <= 6 else "high"


def classify_action(action: dict, summary: str) -> dict:
    raw = CLASSIFIER.ask(
        f"Risk context:\n{CONTEXT}\n\nOverall task: {summary}\n\nEvaluate this action:\n"
        f"  Action : {action['action']}\n  Type   : {action['type']}\n  Target : {action['target']}\n"
        f"  Outcome: {action['expected_outcome']}\n\n"
        "Consider: can it be undone quickly, who or what is affected (local, team, system-wide, external), "
        "and whether it touches sensitive data or shared systems. Score it 1-10 (1-3 low, 4-6 medium, "
        "7-10 high).\n\nReturn ONLY JSON:\n"
        '{"risk_score": <1-10>, "reversibility": "easily reversible|reversible within window|hard to reverse|irreversible", '
        '"impact_scope": "local|team-wide|system-wide|external", '
        '"data_sensitivity": "public|internal|confidential|secret", "reasoning": "2-3 sentences"}')
    data = _extract_json(raw)
    try:
        score = max(1, min(10, int(data.get("risk_score", 5))))
    except (TypeError, ValueError):
        score = 5
    level = level_for(score)
    return {"risk_score": score, "risk_level": level, "approval_required": level == "high",
            "reversibility": str(data.get("reversibility", "unknown")),
            "impact_scope": str(data.get("impact_scope", "unknown")),
            "data_sensitivity": str(data.get("data_sensitivity", "internal")),
            "reasoning": str(data.get("reasoning", "Risk assessment completed."))}


def approval_card(action: dict) -> str:
    """The text a reviewer sees. In a real team this would arrive as a pull request or a chat message."""
    return (f"Approval requested for action {action['index']}\n\n"
            f"Action: {action['action']}\nType: {action['type']}  ·  Target: {action['target']}\n"
            f"Expected outcome: {action['expected_outcome']}\n\n"
            f"Risk score: {action['risk_score']}/10 (high)\n"
            f"Reversibility: {action['reversibility']}  ·  Scope: {action['impact_scope']}  ·  "
            f"Data: {action['data_sensitivity']}\nWhy: {action['reasoning']}")
