"""Generator — writes the first draft, then refines it using the critic's must-fix list."""

from shared.agent import Agent
from shared.codeutil import extract_code

PERSONA = ("You are an expert Python engineer with deep experience writing correct, secure, readable code. "
           "You are meticulous and you address every concern a reviewer raises.")

GENERATOR = Agent("Generator", PERSONA, temperature=0.3)

FORMAT = ("Reply with ONE ```python block containing the complete file and nothing else in it, then one line "
          "starting with `Rationale:` that briefly explains your approach.")


def _split(raw: str) -> tuple[str, str]:
    """Return (code, rationale) from a reply."""
    code = extract_code(raw)
    rationale = raw.rsplit("```", 1)[-1].strip() if "```" in raw else ""
    return code, rationale.removeprefix("Rationale:").strip() or "Draft produced."


def draft(spec: str, entry: str) -> tuple[str, str]:
    """Iteration 1: a first draft from the specification alone."""
    raw = GENERATOR.ask(
        f"Task:\n{spec}\n\nWrite the complete `{entry}`. Aim for correct, secure, efficient, readable "
        f"code with proper error handling.\n\n{FORMAT}")
    return _split(raw)


def refine(spec: str, entry: str, previous: str, critique: dict) -> tuple[str, str]:
    """Iteration 2 and later: improve the previous draft using the critique."""
    issues = "\n".join(f"  {i + 1}. {m}" for i, m in enumerate(critique["must_fix"])) or "  (none listed)"
    raw = GENERATOR.ask(
        f"Task:\n{spec}\n\nYour previous draft of `{entry}`:\n```python\n{previous}```\n\n"
        f"The critic scored it {critique['overall_score']}/10.\n"
        f"Critic's feedback: {critique['overall_feedback']}\n\n"
        f"MUST-FIX issues (address ALL of them):\n{issues}\n\n"
        "Write an improved version that fixes every must-fix issue. Do not regress on what was already "
        f"good.\n\n{FORMAT}")
    return _split(raw)
