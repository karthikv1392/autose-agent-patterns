"""Multi-agent pattern 5 — Skill Repository (reuse what worked in an earlier session).

   task ─► [search the library] ─► retrieved skills ─┐
              ▲  (summaries only)                     ▼
              │                              [solve: adapt or write] ─► code ─► [run the tests]
              │                                                                        │ green
              └──────────────── [save as a new skill] ◄───────────────────────────────┘

Why it matters for software engineering
---------------------------------------
Teams solve the same kinds of problems again and again: input validation, retries with backoff,
strict parsers, API checklists. A stateless agent starts from zero every time. A skill repository
lets it search earlier solutions before writing code, adapt the ones that fit, and save new work
for next time. The library persists on disk, so the agent improves across sessions, not within one.

Only solutions that pass the tests are saved. Otherwise a wrong solution would be retrieved later
and repeat its mistake. Try it: run `parse_duration`, then `roman_to_int`. Both are strict parsers
with fiddly rules, so the second run may find a skill worth reusing. Whether it does depends on the
model, because the search is the model's judgement. `merge_intervals` is unrelated, so the search
should decline.

(Generic version: Multi_Agent_Pattern/patterns/p11_skill_library in the Agentic_Patterns repo.)
"""

from patterns.m05_skill_repository.skill_agent import search_skills, solve
from patterns.m05_skill_repository.skill_store import SkillStore, make_skill
from shared.sandbox import run_tests
from shared.tasks import load_task
from shared.trace import Trace


def run(task_key: str, trace: Trace | None = None, top_k: int = 2, store: SkillStore | None = None) -> dict:
    trace = trace or Trace()
    store = store or SkillStore()
    task = load_task(task_key)
    size_before = store.size()

    trace.add("Task", task.spec, agent="user")
    trace.add("Skill library before this run", kind="table", agent="Library", data=[
        {"skill": s.name, "tags": ", ".join(s.tags), "times reused": s.use_count} for s in store.all_skills()])

    # ── 1. Search ────────────────────────────────────────────────────────
    trace.add("1 · Search the library", kind="step")
    found = search_skills(store, task.spec, top_k)
    names = ", ".join(s.name for s in found["retrieved"]) or "none"
    trace.add(f"Retrieved: {names}", f"{found['reasoning']}\n\n(Searched {found['searched']} skill summaries.)",
              agent="Skill Agent")

    # ── 2. Solve ─────────────────────────────────────────────────────────
    trace.add("2 · Solve, adapting what was retrieved", kind="step")
    result = solve(task.spec, task.entry, found["retrieved"])
    trace.add(f"Approach: {result['approach']}", kind="code", lang="python", body=result["code"], agent="Skill Agent")

    # ── 3. Verify ────────────────────────────────────────────────────────
    trace.add("3 · Run the hidden tests", kind="step")
    report = run_tests({task.entry: result["code"]}, task.tests)
    trace.add(f"Sandbox: {report.summary()}", report.output, kind="tests", ok=report.ok, agent="Sandbox")

    # ── 4. Save ──────────────────────────────────────────────────────────
    trace.add("4 · Save as a skill", kind="step")
    saved = report.ok and result["is_reusable"]
    if saved:
        store.add(make_skill(result["name"], result["description"], result["tags"],
                             f"{task.title}. {task.summary}", result["code"]))
        trace.add(f"Saved: {result['name']}", f"{result['description']}\n\nTags: {', '.join(result['tags'])}",
                  agent="Library")
    else:
        why = "the tests did not pass, so it is not validated" if not report.ok else "the agent judged it too specific to reuse"
        trace.add("Not saved", f"The solution is not added to the library: {why}.", agent="Library")

    return {
        "solved": report.ok,
        "headline": (f"{report.summary()} · retrieved {len(found['retrieved'])} skill(s) · "
                     f"library {size_before} → {store.size()} skills"),
        "report": report,
        "files": {task.entry: result["code"]},
        "stats": {"retrieved": [s.name for s in found["retrieved"]], "approach": result["approach"],
                  "skills_before": size_before, "skills_after": store.size()},
    }


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "parse_duration")
