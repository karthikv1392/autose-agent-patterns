"""Multi-agent pattern 7 — Human-in-the-Loop Approval (a person decides on the risky actions).

   task ─► [Planner] ─► actions ─► [Risk classifier] ─┬─ low / medium ──────────────► run automatically ─┐
                                      (score 1-10)    │                                                  ├─► [Executor] ─► tests
                                                      └─ high ─► approval card ─► [Human] ─ approve ────┘
                                                                                      └─ reject ─► skipped
                                            every step is written to the audit trail

Why it matters for software engineering
---------------------------------------
A coding agent can edit files, change dependencies, rewrite CI configuration, push and deploy. Some of
those are easy to undo and some are not, and an agent that treats a test run and a force-push alike
leaves nobody accountable. The planner covers delivery as well as the fix, because an autonomous engineer is not done until the change
ships. Here each action gets a risk score. Low and medium risk actions run on
their own, high-risk actions wait for a named reviewer to approve or reject them, and the audit trail
records who decided what.

The demo works in two phases so a person can sit between them: `plan()` plans and classifies, then
`execute()` applies the decisions. A high-risk action with no decision counts as rejected. Edits to the
project's own files and test runs are real; deploys, dependencies and shell commands are simulated.
After execution the hidden tests show what the decisions cost or saved.

(Generic version: Multi_Agent_Pattern/patterns/p08_human_in_the_loop in the Agentic_Patterns repo.)
"""

import sys
from typing import Callable

from patterns.m07_human_approval.audit import AuditTrail
from patterns.m07_human_approval.executor import execute_action
from patterns.m07_human_approval.planner import plan_actions
from patterns.m07_human_approval.risk import approval_card, classify_action
from shared.diffutil import unified_diff
from shared.sandbox import run_tests
from shared.tasks import load_task
from shared.trace import Trace

Decision = dict          # {"status": "approved" | "rejected", "approver": str, "notes": str}


def plan(task_key: str, trace: Trace | None = None, num_actions: int = 6) -> dict:
    """Phase 1: plan the actions, score their risk and prepare the approval cards."""
    trace = trace or Trace()
    task = load_task(task_key)
    audit = AuditTrail()
    trace.add("Task", task.spec, agent="user")

    trace.add("1 · Plan the actions", kind="step")
    plan_ = plan_actions(task.spec, task.starter, num_actions)
    trace.add("Plan", plan_["summary"], agent="Planner")

    trace.add("2 · Classify the risk of each action", kind="step")
    actions = []
    for a in plan_["actions"]:
        action = {**a, **classify_action(a, plan_["summary"])}
        audit.log(action, "planned", notes=f"{action['reversibility']} · scope {action['impact_scope']}")
        if action["approval_required"]:
            action["card"] = approval_card(action)
            audit.log(action, "notified", notes="approval card sent to the reviewer")
        actions.append(action)
    trace.add("Planned actions and their risk", kind="table", agent="Risk classifier", data=[
        {"#": a["index"], "action": a["action"], "type": a["type"], "risk": f"{a['risk_level']} ({a['risk_score']})",
         "needs approval": "yes" if a["approval_required"] else "no", "why": a["reasoning"]} for a in actions])
    high = [a for a in actions if a["approval_required"]]
    trace.add(f"{len(high)} action(s) need a human decision", "\n\n---\n\n".join(a["card"] for a in high) or "None.",
              agent="Notifier")
    return {"task": task, "summary": plan_["summary"], "actions": actions, "audit": audit}


def execute(state: dict, decisions: dict[int, Decision], trace: Trace | None = None) -> dict:
    """Phase 2: apply the human's decisions and run what is allowed."""
    trace = trace or Trace()
    task, audit = state["task"], state["audit"]
    files = dict(task.starter)
    counts = {"auto": 0, "approved": 0, "rejected": 0, "simulated": 0}

    trace.add("3 · Decisions and execution", kind="step")
    for a in state["actions"]:
        label = f"Action {a['index']} ({a['risk_level']}, {a['risk_score']}/10): {a['action']}"
        if a["approval_required"]:
            d = decisions.get(a["index"]) or {"status": "rejected", "approver": "system", "notes": "no decision was given"}
            approved = d.get("status") == "approved"
            audit.log(a, "approved" if approved else "rejected", actor=d.get("approver", "reviewer"), notes=d.get("notes", ""))
            if not approved:
                audit.log(a, "skipped", notes="rejected, so it was not run")
                counts["rejected"] += 1
                trace.add(f"{label}: rejected by {d.get('approver', 'reviewer')}", d.get("notes", "") or "No note given.",
                          agent="Human")
                continue
            counts["approved"] += 1
        else:
            audit.log(a, "auto_approved", notes="low or medium risk" + ("; flagged for awareness" if a["risk_level"] == "medium" else ""))
            counts["auto"] += 1

        before = files
        result = execute_action(a, files, task.spec, task.tests)
        files = result["files"]
        counts["simulated"] += result["simulated"]
        audit.log(a, "executed", notes=result["outcome"])
        diff = unified_diff(before, files)
        if diff:
            trace.add(f"{label}: {result['outcome']}", diff, kind="code", lang="diff", agent="Executor")
        else:
            trace.add(f"{label}: {result['outcome']}", agent="Executor")

    trace.add("4 · Audit trail and hidden tests", kind="step")
    trace.add("Audit trail", kind="table", agent="Audit", data=[
        {"#": r["seq"], "action": r["action_index"], "event": r["event"], "by": r["actor"], "notes": r["notes"]}
        for r in audit.rows()])
    report = run_tests(files, task.tests)
    trace.add(f"Hidden tests on the final project: {report.summary()}", report.output, kind="tests", ok=report.ok,
              agent="Sandbox")

    return {
        "solved": report.ok,
        "headline": (f"{counts['auto']} ran automatically · {counts['approved']} approved · {counts['rejected']} rejected"
                     f" · {counts['simulated']} simulated · {report.summary()}"),
        "report": report,
        "files": files,
        "audit": audit.rows(),
        "stats": counts,
    }


def cli_decide(action: dict) -> Decision:
    """Ask the person at the terminal. With no terminal, reject: the safe default."""
    if not sys.stdin.isatty():
        return {"status": "rejected", "approver": "system", "notes": "no reviewer present"}
    print("\n" + action["card"])
    answer = input("Approve this action? [y/N] ").strip().lower()
    name = input("Your name: ").strip() or "reviewer"
    return {"status": "approved" if answer == "y" else "rejected", "approver": name, "notes": ""}


def run(task_key: str, trace: Trace | None = None, num_actions: int = 6,
        decide: Callable[[dict], Decision] | None = None) -> dict:
    """Both phases in one call. `decide` is asked about each high-risk action; the default asks the terminal."""
    trace = trace or Trace()
    state = plan(task_key, trace, num_actions)
    decide = decide or cli_decide
    decisions = {a["index"]: decide(a) for a in state["actions"] if a["approval_required"]}
    return execute(state, decisions, trace)


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "cart_bugs")
