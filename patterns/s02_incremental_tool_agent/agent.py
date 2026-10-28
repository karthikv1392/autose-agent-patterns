"""Single-agent pattern 2 — Incremental Tool Agent.

The agent queries the LLM several times; each round sees the goal plus every
earlier round, so the decision is built up step by step:

   Round 1  Analyse the bug report            (what is wrong? what do I need to see?)
   Round 2  Plan + choose a tool              (which developer tool gets me that?)
   Round 3  Exact tool parameters (JSON)      (which file? which pattern?)
   Execute  Run the tool in the project
   Synthesis  goal + reasoning + tool output  ->  complete fixed files  ->  tests

Why it matters for software engineering
---------------------------------------
"Which tool, with which arguments?" is the core decision of any coding agent
(read a file? grep? run tests?). Splitting it into small, inspectable rounds makes
a wrong choice easy to see and debug — you can read exactly where the reasoning
went off. Compare with a one-step agent that makes all three decisions in a single
call.

(Existing repo analogue: Single_Agent_Pattern/patterns/p06_incremental_tool_agent.)
"""

import json
import re

from patterns.s02_incremental_tool_agent.tools import make_tools, tool_descriptions
from shared.codeutil import extract_files
from shared.diffutil import unified_diff
from shared.llm import generate
from shared.sandbox import run_tests
from shared.tasks import load_task
from shared.trace import Trace


def _extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text) or re.search(r"(\{[\s\S]*\})", text)
    return json.loads(match.group(1).strip())


def run(task_key: str, trace: Trace | None = None) -> dict:
    trace = trace or Trace()
    task = load_task(task_key)
    goal = task.spec
    tools = make_tools(task.starter, task.tests)
    project = f"Project files: {', '.join(sorted(task.starter))} (plus test_suite.py)."

    trace.add("Bug report", goal, agent="user")

    # ── Round 1: goal analysis ───────────────────────────────────────────
    trace.add("Round 1 · Analyse the problem", kind="step")
    r1 = generate(
        f'Goal: "{goal}"\n{project}\n\n'
        "Analyse this bug report. What is the likely problem, and what information do you need "
        "to see before you can fix it? Do NOT propose a fix yet.", temperature=0.2)
    trace.add("Analysis", r1, agent="Agent")

    # ── Round 2: plan + tool selection ───────────────────────────────────
    trace.add("Round 2 · Plan and choose a tool", kind="step")
    r2 = generate(
        f'Goal: "{goal}"\n{project}\n\n=== Round 1 ===\n{r1}\n===\n\n'
        "Write a short numbered plan (3-4 steps) and choose the SINGLE best tool to call first, "
        "explaining why. You already know the file names, so pick the tool that reveals what you still "
        "cannot see (the code or the failures).\n\n"
        f"Available tools:\n{tool_descriptions(tools)}\n\nDo NOT give exact parameters yet.", temperature=0.2)
    trace.add("Plan and tool choice", r2, agent="Agent")

    # ── Round 3: exact parameters ────────────────────────────────────────
    trace.add("Round 3 · Exact tool call", kind="step")
    r3 = generate(
        f'Goal: "{goal}"\n{project}\n\n=== Round 1 ===\n{r1}\n===\n\n=== Round 2 ===\n{r2}\n===\n\n'
        f"Available tools:\n{tool_descriptions(tools)}\n\n"
        "Finalise the call. Use EXACTLY the keys selected_tool and parameters. Respond with JSON only, e.g.\n"
        '```json\n{"selected_tool": "read_file", "parameters": {"path": "example.py"}}\n```',
        temperature=0.1)
    trace.add("Tool call (JSON)", r3, kind="code", lang="json", agent="Agent")

    try:
        spec = _extract_json(r3)
        # Small models drift from the requested key names; accept the common aliases.
        name = spec.get("selected_tool") or spec.get("tool_name") or spec.get("tool") or "none"
        params = spec.get("parameters") or spec.get("tool_input") or spec.get("params") or spec.get("args") or {}
    except Exception:
        name, params = "none", {}

    # ── Execute ──────────────────────────────────────────────────────────
    trace.add("Execute the tool", kind="step")
    if name in tools:
        try:
            output = tools[name]["fn"](**params)
        except TypeError as e:
            output = f"ERROR calling {name}: {e}"
    else:
        output = f"Tool '{name}' not found."
    trace.add(f"Tool output: {name}({json.dumps(params)})", output, kind="code", lang="python", agent="Tool")

    # ── Synthesis: write the fix ─────────────────────────────────────────
    trace.add("Synthesis · Write the fix", kind="step")
    raw = generate(
        f'Goal: "{goal}"\n{project}\n\nYour analysis:\n{r1}\n\nYour plan:\n{r2}\n\n'
        f"Tool used: {name} {json.dumps(params)}\nTool output:\n```\n{output}\n```\n\n"
        "Now fix the bug. Return the COMPLETE updated content of each file you change as:\n"
        "### FILE: <name>.py\n```python\n<full file>\n```\n"
        "Read docstrings for intended behaviour. If the tool output did not show the code you need, "
        "say so briefly and still make your best attempt for the files named in the project list.",
        temperature=0.2)
    fixed = {**task.starter, **{k: v for k, v in extract_files(raw).items() if k in task.starter}}
    trace.add("Patch", unified_diff(task.starter, fixed) or "(no changes parsed)", kind="code", lang="diff", agent="Agent")

    report = run_tests(fixed, task.tests)
    trace.add(f"Sandbox: {report.summary()}", report.output, kind="tests", ok=report.ok, agent="Sandbox")

    return {
        "solved": report.ok,
        "headline": f"Chose tool '{name}' → {report.summary()}",
        "report": report,
        "files": fixed,
        "stats": {"tool": name},
    }


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "pager_bugs")
