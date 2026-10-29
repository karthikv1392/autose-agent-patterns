"""Executor — carries out one allowed action.

Real, inside the sandbox:   read a project file, edit a project file, run the tests.
Simulated, nothing runs:    commands, dependencies, deploys, deletes, and edits to files that are not
                            part of the project. The demo never touches real infrastructure, and the
                            outcome says so.
"""

from shared.agent import Agent
from shared.codeutil import extract_code
from shared.sandbox import run_tests

EDITOR = Agent("Executor", "You are a careful Python engineer. You make exactly the change you are asked to "
               "make, keep everything else as it is, and reply with the complete updated file.", temperature=0.2)


def execute_action(action: dict, files: dict[str, str], spec: str, tests: str) -> dict:
    """Return {"executed", "simulated", "outcome", "files"} where files is the project after the action."""
    kind, target = action["type"], action["target"]

    targets = [t.strip() for t in target.split(",")]          # a read may name several files
    if kind == "read" and all(t in files for t in targets):
        lines = sum(len(files[t].splitlines()) for t in targets)
        return {"executed": True, "simulated": False, "files": files,
                "outcome": f"Read {', '.join(targets)} ({lines} lines)."}
    if kind == "test":
        report = run_tests(files, tests)
        return {"executed": True, "simulated": False, "files": files, "outcome": f"Ran the tests: {report.summary()}."}
    if kind == "edit" and target in files:
        raw = EDITOR.ask(f"Task:\n{spec}\n\nCurrent `{target}`:\n```python\n{files[target]}```\n\n"
                         f"Make this change: {action['action']}\nExpected outcome: {action['expected_outcome']}\n\n"
                         f"Reply with ONE ```python block containing the complete updated `{target}`.")
        return {"executed": True, "simulated": False, "files": {**files, target: extract_code(raw)},
                "outcome": f"Edited {target}."}
    return {"executed": True, "simulated": True, "files": files,
            "outcome": f"Simulated: a '{kind}' action on '{target}'. Nothing was run or changed."}
