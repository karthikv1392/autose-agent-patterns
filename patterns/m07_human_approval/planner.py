"""Planner — turns the task into a list of discrete actions the agent would take.

The prompt asks for a realistic mix of routine and consequential actions, so that the risk
classification and the approval step have something to decide.
"""

import json
import re

from shared.agent import Agent

PERSONA = ("You are an autonomous software engineer about to carry out a task on a real project. "
           "You plan your work as concrete, separate actions, the way you would actually do it.")

PLANNER = Agent("Planner", PERSONA, temperature=0.3)

ACTION_TYPES = ["read", "edit", "test", "command", "dependency", "deploy", "delete"]


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


def _fallback(files: dict[str, str]) -> list[dict]:
    """A plain read, edit, test plan, used when the model's reply cannot be parsed."""
    actions = [{"action": f"Read {name}", "type": "read", "target": name, "expected_outcome": "Understand the code"}
               for name in sorted(files)]
    actions += [{"action": f"Fix the problems in {name}", "type": "edit", "target": name,
                 "expected_outcome": "Code matches the specification"} for name in sorted(files)]
    actions.append({"action": "Run the test suite", "type": "test", "target": "test_suite.py",
                    "expected_outcome": "All tests pass"})
    return actions


def plan_actions(spec: str, files: dict[str, str], num_actions: int) -> dict:
    listing = "\n".join(f"- {name} ({len(src.splitlines())} lines)" for name, src in sorted(files.items()))
    raw = PLANNER.ask(
        f"Task:\n{spec}\n\nProject files:\n{listing}\n\n"
        f"Break this task into exactly {num_actions} discrete, sequential actions, in the order you would do them. "
        "Each must be concrete and a single operation. The work is only finished when the change has been "
        "delivered, so plan the delivery as well as the fix. Include a realistic mix:\n"
        "  - 2-3 routine actions: reading a file, running the tests (low risk)\n"
        "  - 1-2 ordinary edits to project files (medium risk)\n"
        "  - 1-2 high-impact or hard-to-reverse actions (high risk), such as force-pushing or pushing to a "
        "shared branch, editing build or CI configuration, adding a dependency, deleting code, changing a "
        "public function's signature or return shape, or deploying\n\n"
        "For each action give:\n"
        '  "action"           one sentence\n'
        f'  "type"             one of {", ".join(ACTION_TYPES)}\n'
        '  "target"           ONE file or system it touches\n'
        '  "expected_outcome" one sentence\n'
        'Return ONLY JSON: {"summary": "one sentence", "actions": [{...}]}')
    data = _extract_json(raw)
    actions = []
    for a in data.get("actions", []) if isinstance(data.get("actions"), list) else []:
        if isinstance(a, dict) and a.get("action"):
            kind = str(a.get("type", "command")).lower()
            actions.append({"action": str(a["action"]), "type": kind if kind in ACTION_TYPES else "command",
                            "target": str(a.get("target", "")), "expected_outcome": str(a.get("expected_outcome", ""))})
    if not actions:
        actions = _fallback(files)
    for i, a in enumerate(actions[:num_actions], 1):
        a["index"] = i
    return {"summary": str(data.get("summary", "")) or spec.splitlines()[0], "actions": actions[:num_actions]}
