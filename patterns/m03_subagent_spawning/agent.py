"""Multi-agent pattern 3 — Sub-agent spawning (dynamic fan-out / fan-in).

                      ┌─► SubAgent A (owns inventory.py) ─┐
   task + codebase ─► [Spawner] ─► SubAgent B (owns pricing.py)   ─┼─► [Integrator] ─► run tests
   (decides WHO and   └─► SubAgent C (owns orders.py)    ─┤        + static checks
    HOW MANY)             SubAgent D (owns reports.py)   ─┘        + PR description
                          (created at runtime, run in parallel)

Why it matters for software engineering
---------------------------------------
Large refactors and migrations decompose naturally by module. A Spawner reads the
repo and creates a worker per slice, each with a persona tailored to what is in its
file. Workers run in parallel with isolated context; an Integrator merges their
files and the project's EXISTING test suite proves behaviour was preserved.

Unlike a fixed pipeline of roles, the team is designed per task.

(Existing repo analogue: Multi_Agent_Pattern/patterns/p10_subagent_spawning.)
"""

import concurrent.futures
import time

from patterns.m03_subagent_spawning.metrics import modernisation_metrics, score_text
from patterns.m03_subagent_spawning.spawner import spawn
from patterns.m03_subagent_spawning.subagent import work
from shared.diffutil import unified_diff
from shared.llm import generate
from shared.sandbox import run_tests
from shared.tasks import load_task
from shared.trace import Trace


def run(task_key: str, trace: Trace | None = None, max_agents: int = 4) -> dict:
    trace = trace or Trace()
    task = load_task(task_key)
    files = task.starter

    trace.add("Task", task.spec, agent="user")
    before_m = modernisation_metrics(files)
    base = run_tests(files, task.tests)
    trace.add("Before", f"{score_text(before_m)}\nExisting tests: {base.summary()}", agent="Harness")

    # ── 1. Spawn ─────────────────────────────────────────────────────────
    trace.add("1 · Spawner designs the team", kind="step")
    plan = spawn(task.spec, files, max_agents)
    trace.add("Strategy", plan["strategy"], agent="Spawner")
    trace.add(f"Spawned {len(plan['specs'])} sub-agents", kind="table", agent="Spawner",
              data=[{"name": s["name"], "owns": s["file"], "special notes": s["instructions"]} for s in plan["specs"]])

    # ── 2. Work in parallel (results logged afterwards, on the main thread) ──
    trace.add("2 · Sub-agents work in parallel", kind="step")
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(plan["specs"])) as pool:
        results = list(pool.map(lambda s: work(s, task.spec, files), plan["specs"]))
    wall = time.time() - start
    merged = dict(files)
    for r in results:
        label = r["spec"]["name"] + (f" — ❌ {r['error']}" if r["error"] else f" — {r['seconds']}s")
        trace.add(label, unified_diff({r["spec"]["file"]: files[r["spec"]["file"]]}, {r["spec"]["file"]: r["code"]}),
                  kind="code", lang="diff", agent=r["spec"]["name"])
        if not r["error"]:
            merged[r["spec"]["file"]] = r["code"]

    # ── 3. Integrate and verify ──────────────────────────────────────────
    trace.add("3 · Integrator merges and verifies", kind="step")
    after_m = modernisation_metrics(merged)
    report = run_tests(merged, task.tests)
    trace.add(f"Existing test suite on merged code: {report.summary()}", report.output,
              kind="tests", ok=report.ok, agent="Sandbox")
    trace.add("After", f"{score_text(after_m)}", agent="Harness")

    pr = generate(
        "Write a concise pull-request description (title + 4 bullets) for this refactor.\n"
        f"Task: {task.spec}\nBefore: {score_text(before_m)}\nAfter: {score_text(after_m)}\n"
        f"Files changed: {', '.join(r['spec']['file'] for r in results if not r['error'])}\n"
        f"Tests: {report.summary()}", temperature=0.3)
    trace.add("PR description (written by the Integrator)", pr, agent="Integrator")

    seq = sum(r["seconds"] for r in results)
    done = after_m["fully_typed"] == after_m["functions"] and after_m["print_calls"] == 0 and report.ok
    return {
        "solved": report.ok and done,
        "headline": (f"{score_text(before_m)}  →  {score_text(after_m)} · tests {report.summary()} · "
                     f"parallel wall time {wall:.0f}s vs {seq:.0f}s sequential"),
        "report": report,
        "files": merged,
        "stats": {"subagents": len(results), "wall_s": round(wall, 1), "sequential_s": round(seq, 1)},
    }


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "legacy_shop")
