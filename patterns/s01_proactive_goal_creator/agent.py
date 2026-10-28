"""Single-agent pattern 1 — Proactive Goal Creator.

   vague request ─┬─► [gather env] ─────┐
                  ├─► [map the repo] ───┤
                  ├─► [run the tests] ──┼─► enriched prompt ─► LLM ─► patch ─► tests
                  └─► [read sources] ───┘

Why it matters for software engineering
---------------------------------------
Real bug reports are vague: "the pager is broken". A passive agent can only guess.
A proactive agent first collects what a developer would look at — the repo layout,
a fresh test run, the code — and folds it into the goal before the LLM sees it.
Same model, same request; the difference in outcome comes entirely from context.

(Existing repo analogue: Single_Agent_Pattern/patterns/p02_proactive_goal_creator.)
"""

from patterns.s01_proactive_goal_creator.context import (
    gather_env_context, gather_repo_map, gather_source, gather_test_status,
)
from shared.codeutil import extract_files, truncate
from shared.diffutil import unified_diff
from shared.llm import generate
from shared.sandbox import run_tests
from shared.tasks import load_task
from shared.trace import Trace

SYSTEM = (
    "You are an expert Python engineer. Fix the bug by returning the COMPLETE updated content of "
    "every file you change, each as:\n### FILE: <name>.py\n```python\n<full file>\n```\n"
    "Do not modify test_suite.py. No other commentary."
)


def run(task_key: str, trace: Trace | None = None) -> dict:
    trace = trace or Trace()
    task = load_task(task_key)
    goal = task.vague_goal or task.spec

    trace.add("User's goal (as typed)", goal, agent="user")

    # ── A. Passive: the goal goes straight to the LLM ────────────────────
    trace.add("A · Passive — goal only", kind="step")
    raw = generate(f"{goal}\n\nThe project is a small Python package.", system=SYSTEM, temperature=0.2)
    passive_files = {**task.starter, **{k: v for k, v in extract_files(raw).items() if k in task.starter}}
    trace.add("Model reply (it has seen no code)", raw, agent="LLM")
    passive = run_tests(passive_files, task.tests)
    trace.add(f"Sandbox: {passive.summary()}", passive.output, kind="tests", ok=passive.ok, agent="Sandbox")

    # ── B. Proactive: collect context first ──────────────────────────────
    trace.add("B · Proactive — gather context, then ask", kind="step")
    env = gather_env_context()
    repo_map = gather_repo_map(task.starter)
    status, test_output = gather_test_status(task.starter, task.tests)
    trace.add("Gathered: environment", env, agent="Context")
    trace.add("Gathered: repository map", repo_map, agent="Context")
    trace.add(f"Gathered: test run before any change — {status}", test_output, kind="tests", ok=False, agent="Context")

    enriched = "\n\n".join([
        f'The user asked: "{goal}"',
        "## Environment\n" + env,
        "## Repository map\n" + repo_map,
        "## Current test results (the bug is whatever makes these fail)\n" + truncate(test_output, 2500),
        "## Source files\n" + gather_source(task.starter),
        "Using ALL of the context above, fix the code so the tests pass. Read each docstring: "
        "it states the intended behaviour.",
    ])
    trace.add("Enriched prompt sent to the LLM", truncate(enriched, 6000), agent="Goal Creator")

    raw = generate(enriched, system=SYSTEM, temperature=0.2)
    fixed = {**task.starter, **{k: v for k, v in extract_files(raw).items() if k in task.starter}}
    trace.add("Patch", unified_diff(task.starter, fixed) or "(no changes parsed)", kind="code", lang="diff", agent="LLM")
    proactive = run_tests(fixed, task.tests)
    trace.add(f"Sandbox: {proactive.summary()}", proactive.output, kind="tests", ok=proactive.ok, agent="Sandbox")

    return {
        "solved": proactive.ok,
        "headline": f"Goal only: {passive.summary()}  →  With proactive context: {proactive.summary()}",
        "report": proactive,
        "files": fixed,
        "stats": {"passive_pass_rate": passive.pass_rate, "proactive_pass_rate": proactive.pass_rate},
    }


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "pager_bugs")
