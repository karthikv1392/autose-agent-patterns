"""Executor — turns the (reflected) plan into code, and revises code after failures."""

from patterns.s03_self_reflection.planner import plan_text
from shared.codeutil import extract_code
from shared.llm import generate

SYSTEM = (
    "You are a senior Python engineer. Standard library only. Reply with ONE ```python block "
    "containing the complete file and nothing else: no tests, no example usage, no explanation."
)


def implement(spec: str, entry: str, steps: list[dict]) -> str:
    prompt = (
        f"Specification:\n{spec}\n\nFollow this plan:\n{plan_text(steps)}\n\n"
        f"Write the complete `{entry}`."
    )
    return extract_code(generate(prompt, system=SYSTEM, temperature=0.2))


def revise(spec: str, entry: str, code: str, test_output: str, diagnoses: list[str]) -> str:
    lessons = "\n\n".join(f"Diagnosis {i}:\n{d}" for i, d in enumerate(diagnoses, 1))
    prompt = (
        f"Specification:\n{spec}\n\nCurrent `{entry}`:\n```python\n{code}```\n\n"
        f"Test results:\n{test_output}\n\nYour own diagnosis:\n{lessons}\n\n"
        f"Write the corrected, complete `{entry}`. Fix every failing test without breaking passing ones. "
        "If earlier patches keep failing on the same tests, stop patching: rewrite the file from scratch "
        "with a simpler design."
    )
    return extract_code(generate(prompt, system=SYSTEM, temperature=0.2))
