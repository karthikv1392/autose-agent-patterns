"""Multi-agent pattern 4 — Swarm (choreography: agents hand work to each other).

                    ┌──────────── "tests failed, small fix" ────────────┐
                    ▼                                                   │
   [Dispatcher] ─► Coder ─► Tester ─► Debugger ─► Tester ─► ... ─► Reviewer ─► done
                      ▲        │ "tests failed badly, rewrite"             │
                      └────────┘                         "changes needed" ─┘ (back to Coder/Debugger)

Why it matters for software engineering
---------------------------------------
There is no fixed pipeline and no central manager. A shared blackboard holds the
current code and the latest test report; each agent does its job and then NAMES who
should act next (`HANDOFF: tester`). The path through the swarm depends on what
actually happens — a clean first draft goes straight to review; a broken one loops
through test → debug → test until the suite is green.

  • Coder    — writes or rewrites the implementation        (LLM)
  • Tester   — runs the real test suite and routes by result (tool: rule-based routing;
               big failure or two fixes without progress -> back to the Coder for a rewrite)
  • Debugger — patches code using the failing output         (LLM)
  • Reviewer — checks spec compliance once tests are green   (LLM)

Compare with a fixed pipeline of roles (plan → code → review): here the control
flow emerges at runtime.

(Existing repo analogue: Multi_Agent_Pattern/patterns/p07_swarm.)
"""

import re

from shared.agent import Agent
from shared.codeutil import extract_code
from shared.sandbox import run_tests
from shared.tasks import load_task
from shared.trace import Trace

CODE_FORMAT = ("Reply with ONE ```python block containing the COMPLETE file, then a final line "
               "`HANDOFF: <agent>` naming who should act next.")

CODER = Agent("Coder", "You are a senior Python engineer who writes clean, correct, standard-library-only "
              "code from a specification. " + CODE_FORMAT + " Hand off to `tester`.", 0.3)
DEBUGGER = Agent("Debugger", "You are a debugging specialist. You read failing test output, find the root "
                 "cause and make the smallest correct fix without breaking passing behaviour. "
                 + CODE_FORMAT + " Hand off to `tester`.", 0.2)
REVIEWER = Agent("Reviewer", "You are a strict code reviewer. The tests are green; you check the code "
                 "against EVERY sentence of the specification for gaps the tests may miss.", 0.2)

VALID_NEXT = {"coder", "tester", "debugger", "reviewer", "done"}


def _handoff(text: str, default: str, allowed: set[str]) -> str:
    m = re.search(r"HANDOFF:\s*`?(\w+)`?", text, re.IGNORECASE)
    target = m.group(1).lower() if m else default
    return target if target in allowed else default


def _code_only(raw: str) -> str:
    """Models sometimes put the HANDOFF line inside the code fence; never ship it as source."""
    code = extract_code(raw)
    return "\n".join(l for l in code.splitlines() if not re.match(r"\s*HANDOFF:", l, re.I)) + "\n"


def run(task_key: str, trace: Trace | None = None, max_hops: int = 12) -> dict:
    trace = trace or Trace()
    task = load_task(task_key)

    # Blackboard — the only shared state.
    code = ""
    report = None
    feedback = ""
    review_requests = 0
    green_code = None          # last version that passed every test
    from_review = False        # True while a reviewer-requested change is being tested
    best_passed, stalls = -1, 0   # progress tracking, used by the Tester to detect a dead end
    best_code, best_rate = "", -1.0   # best version seen so far (returned if the swarm runs out of hops)
    path = ["dispatcher"]

    trace.add("Task", task.spec, agent="user")
    trace.add("Swarm starts", "Dispatcher hands the task to **coder**. After that, agents route themselves.",
              agent="Dispatcher")
    current = "coder"

    for hop in range(1, max_hops + 1):
        path.append(current)
        trace.add(f"Hop {hop} → {current}", kind="step")

        if current == "coder":
            note = f"\n\nYour previous attempt failed badly:\n{feedback}\nRewrite it from scratch with a simpler design." if code else ""
            raw = CODER.ask(f"Write the complete `{task.entry}`.\n\n{task.spec}{note}")
            code = _code_only(raw)
            trace.add("Coder writes the implementation", code, kind="code", lang="python", agent="Coder")
            current = _handoff(raw, "tester", {"tester"})

        elif current == "tester":
            report = run_tests({task.entry: code}, task.tests)
            if report.pass_rate > best_rate:
                best_code, best_rate = code, report.pass_rate
            trace.add(f"Tester: {report.summary()}", report.output, kind="tests", ok=report.ok, agent="Tester")
            # Rule-based routing: this agent is a tool, not an LLM.
            if report.ok:
                green_code, from_review, current = code, False, "reviewer"
            elif from_review and green_code is not None:
                # Veto: a reviewer-requested edit broke a green suite -> keep the last good version.
                trace.add("Tester vetoes the change", "The requested edit broke previously passing tests. "
                          "Reverting to the last green version and finishing.", agent="Tester")
                code, from_review, current = green_code, False, "done"
            else:
                stalls = 0 if report.passed > best_passed else stalls + 1
                best_passed = max(best_passed, report.passed)
                feedback = report.output
                if report.pass_rate < 0.5 or stalls >= 2:
                    current, stalls, best_passed = "coder", 0, -1     # patching is not working: rewrite
                else:
                    current = "debugger"
            trace.add("Tester routes the work", f"→ **{current}**", agent="Tester")

        elif current == "debugger":
            raw = DEBUGGER.ask(
                f"Specification:\n{task.spec}\n\nCurrent code:\n```python\n{code}```\n\n"
                f"Feedback to address:\n{feedback}\n\nFix the code.")
            code = _code_only(raw)
            trace.add("Debugger patches the code", code, kind="code", lang="python", agent="Debugger")
            current = _handoff(raw, "tester", {"tester"})

        elif current == "reviewer":
            raw = REVIEWER.ask(
                f"Specification:\n{task.spec}\n\nCode (all tests pass):\n```python\n{code}```\n\n"
                "Does the code satisfy every rule in the specification? Reply with `VERDICT: APPROVE` or "
                "`VERDICT: CHANGES` plus a short list of required changes, then a final line "
                "`HANDOFF: done` (approve) or `HANDOFF: debugger` (changes).")
            approve = "VERDICT: APPROVE" in raw.upper() or review_requests >= 2
            trace.add("Reviewer: " + ("approves" if approve else "requests changes"), raw, agent="Reviewer")
            if approve:
                current = "done"
            else:
                review_requests += 1
                feedback, current, from_review = f"Reviewer comments:\n{raw}", "debugger", True

        if current == "done":
            path.append("done")
            break
    else:
        path.append("(hop limit)")

    if best_rate >= 0 and current != "done":
        code = best_code            # out of hops: return the best version, not the latest
    final = run_tests({task.entry: code}, task.tests)
    trace.add("Hand-off path", " → ".join(path), agent="Swarm")
    return {
        "solved": final.ok,
        "headline": f"{final.summary()} after {hop} hop(s): {' → '.join(path)}",
        "report": final,
        "files": {task.entry: code},
        "stats": {"hops": hop, "path": path},
    }


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "lru_cache")
