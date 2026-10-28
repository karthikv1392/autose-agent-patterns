"""Single-agent pattern 3 — Self-Reflection.

   spec ─► [Planner] ─► draft plan ─► [Reflector: critique the plan] ─► revised plan
                                                                            │
                         ┌──────────────────────────────────────────────────┘
                         ▼
                    [Executor: write code] ─► [Sandbox: run tests]
                         ▲                          │ fail
                         │                          ▼
                         └─── revised code ◄── [Reflector: diagnose failures]

Why it matters for software engineering
---------------------------------------
The agent checks its own reasoning at two points:

  1. Before acting  — the plan is audited against the spec (cheap: no code written yet).
  2. After acting   — failures are diagnosed in words before the code is edited.

Software has something most domains lack: executable ground truth. The second
reflection is therefore grounded in real test output rather than the model's opinion.
It is still ONE agent with one context — contrast with the multi-agent patterns,
where different agents hold different roles.

(Existing repo analogue: Single_Agent_Pattern/patterns/p09_self_reflection.)
"""

from patterns.s03_self_reflection.executor import implement, revise
from patterns.s03_self_reflection.planner import create_plan, plan_text
from patterns.s03_self_reflection.reflector import reflect_on_failures, reflect_on_plan
from shared.sandbox import run_tests
from shared.tasks import load_task
from shared.trace import Trace


def run(task_key: str, trace: Trace | None = None, max_revisions: int = 3) -> dict:
    trace = trace or Trace()
    task = load_task(task_key)
    trace.add("Task", task.spec, agent="user")

    # ── 1. Plan ──────────────────────────────────────────────────────────
    trace.add("1 · Plan", kind="step")
    plan = create_plan(task.spec)
    trace.add("Draft plan", plan_text(plan), agent="Planner")

    # ── 2. Reflect on the plan (before any code exists) ──────────────────
    trace.add("2 · Reflect on the plan", kind="step")
    reflection = reflect_on_plan(task.spec, plan)
    issues = "\n".join(f"- {i}" for i in reflection["issues"]) or "- none found"
    trace.add("Plan critique" + (" — revised" if reflection["changes_made"] else " — plan judged sound"),
              f"{reflection['reflection_text']}\n\n**Issues**\n{issues}", agent="Reflector")
    final_plan = reflection["revised_steps"]
    if reflection["changes_made"]:
        trace.add("Revised plan", plan_text(final_plan), agent="Reflector")

    # ── 3. Execute, test, and reflect on failures ────────────────────────
    trace.add("3 · Implement and test", kind="step")
    code = implement(task.spec, task.entry, final_plan)
    trace.add("Executor writes the code", code, kind="code", lang="python", agent="Executor")
    report = run_tests({**task.starter, task.entry: code}, task.tests)
    trace.add(f"Sandbox: {report.summary()}", report.output, kind="tests", ok=report.ok, agent="Sandbox")
    first_rate = report.pass_rate

    diagnoses: list[str] = []
    revisions = 0
    while not report.ok and revisions < max_revisions:
        revisions += 1
        trace.add(f"4 · Revision {revisions}", kind="step")
        diagnoses.append(reflect_on_failures(task.spec, code, report.output, diagnoses))
        trace.add("Reflector diagnoses the failures", diagnoses[-1], agent="Reflector")
        code = revise(task.spec, task.entry, code, report.output, diagnoses)
        trace.add("Executor revises the code", code, kind="code", lang="python", agent="Executor")
        report = run_tests({**task.starter, task.entry: code}, task.tests)
        trace.add(f"Sandbox: {report.summary()}", report.output, kind="tests", ok=report.ok, agent="Sandbox")

    return {
        "solved": report.ok,
        "headline": (f"{'Solved' if report.ok else 'Not solved'}: plan {'revised' if reflection['changes_made'] else 'unchanged'}, "
                     f"{revisions} post-test revision(s), final {report.summary()}"),
        "report": report,
        "files": {task.entry: code},
        "stats": {"plan_revised": reflection["changes_made"], "revisions": revisions, "first_try_pass_rate": first_rate},
    }


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "parse_duration")
