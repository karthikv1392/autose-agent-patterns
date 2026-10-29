"""Multi-agent pattern 6 — Generator-Critic Loop (draft, review, revise until a gate passes).

   spec ─► [Generator] ─► draft ─► [Critic] ─► score + must-fix list ─► quality gate
              ▲                                                            │
              │              score < 7 or must-fix not empty               │ pass
              └────────────── revise using the critique ◄──────────────────┘ ─► accepted code

Why it matters for software engineering
---------------------------------------
A model that writes code cannot reliably see its own omissions, and a review that never leads to a
revision improves nothing. Here a separate Critic scores each draft against explicit criteria
(correctness, security, efficiency, readability, error handling) and returns a must-fix list. The
Generator revises against that list, and the loop stops when the gate passes or the iteration
budget runs out.

The Critic only reads the code. After every iteration the demo also runs the real tests, but the
Generator never sees the result. Compare the two columns: a passing critique does not guarantee
passing tests, and that gap is the main limit of this pattern.

(Generic version: Multi_Agent_Pattern/patterns/p09_generator_critic in the Agentic_Patterns repo.)
"""

from patterns.m06_generator_critic.critic import critique
from patterns.m06_generator_critic.generator import draft, refine
from shared.sandbox import run_tests
from shared.tasks import load_task
from shared.trace import Trace


def run(task_key: str, trace: Trace | None = None, max_iterations: int = 4) -> dict:
    trace = trace or Trace()
    task = load_task(task_key)
    trace.add("Task", task.spec, agent="user")

    history = []                       # (score, critic_passed, tests report, code) per iteration
    code, review = "", None
    for i in range(1, max_iterations + 1):
        trace.add(f"Iteration {i}", kind="step")

        # ── Generate or refine ───────────────────────────────────────────
        code, rationale = draft(task.spec, task.entry) if review is None else refine(task.spec, task.entry, code, review)
        trace.add(f"Draft v{i}: {rationale}", code, kind="code", lang="python", agent="Generator")

        # ── Critique (reads the code, does not run it) ───────────────────
        review = critique(task.spec, code, i)
        trace.add("Critic's scores", kind="table", agent="Critic", data=[
            {"criterion": c, "score": r["score"], "severity": r["severity"], "feedback": r["feedback"]}
            for c, r in review["criteria_scores"].items()])
        must_fix = "\n".join(f"- {m}" for m in review["must_fix"]) or "- none"
        gate = "PASS" if review["passed"] else "FAIL"
        trace.add(f"Quality gate: {gate} (overall {review['overall_score']}/10)",
                  f"{review['overall_feedback']}\n\n**Must fix**\n{must_fix}", agent="Critic")

        # ── Ground truth, never shown to the Generator ───────────────────
        report = run_tests({task.entry: code}, task.tests)
        trace.add(f"Hidden tests on this draft: {report.summary()} (the Generator does not see this)",
                  report.output, kind="tests", ok=report.ok, agent="Sandbox")
        history.append((review["overall_score"], review["passed"], report, code))
        if review["passed"]:
            break

    first, last = history[0], history[-1]
    trace.add("Per-iteration summary", kind="table", agent="Loop", data=[
        {"iteration": n, "critic score": s, "critic": "pass" if p else "fail", "hidden tests": r.summary()}
        for n, (s, p, r, _) in enumerate(history, 1)])

    verdict = "passed the gate" if last[1] else f"stopped at the {max_iterations}-iteration limit"
    return {
        "solved": last[2].ok,
        "headline": (f"Critic {verdict} after {len(history)} iteration(s), score {first[0]} → {last[0]} · "
                     f"hidden tests: {last[2].summary()}"),
        "report": last[2],
        "files": {task.entry: last[3]},
        "stats": {"iterations": len(history), "critic_passed": last[1], "initial_score": first[0],
                  "final_score": last[0], "tests_per_iteration": [h[2].pass_rate for h in history]},
    }


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "parse_duration")
