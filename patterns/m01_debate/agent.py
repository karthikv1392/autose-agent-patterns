"""Multi-agent pattern 1 — Debate (adversarial code review).

   PR diff ─► Security ─┐                 ┌─► Security ─┐
              Correctness├─ Round 0 ─────►│  Correctness├─ Round 1..K ─► [Judge] ─► verdict + patched code
              Maintainer ┘  (opening)     └─► Maintainer┘  (rebuttals)                    │
                                                                                  run the tests

Why it matters for software engineering
---------------------------------------
A single reviewer has blind spots; a security-minded reviewer, a correctness-minded
reviewer and a pragmatic maintainer notice *different* things and, crucially, push
back on each other (e.g. "that fix would change the return type and break callers").
Debate surfaces trade-offs that a single pass hides. A Judge then merges the
discussion into a verdict and a patched file — which we verify against real tests.

(Existing repo analogue: Multi_Agent_Pattern/patterns/p03_debate_cooperation.)
"""

from shared.agent import Agent
from shared.codeutil import extract_code, extract_sections
from shared.llm import generate
from shared.sandbox import run_tests
from shared.tasks import load_task
from shared.trace import Trace

DEBATERS = [
    Agent("Security Engineer",
          "You are an application-security engineer reviewing a pull request. You hunt for injection, "
          "unsafe input handling and data exposure, and you insist on concrete, minimal fixes."),
    Agent("Correctness Reviewer",
          "You are a meticulous reviewer who thinks about edge cases: empty results, None, ordering, "
          "off-by-one, wrong semantics versus the docstring. You mentally run the code on awkward inputs."),
    Agent("Pragmatic Maintainer",
          "You are the maintainer who must live with this code. You care about backwards compatibility "
          "(existing callers!), small diffs and not over-engineering. You push back on changes that "
          "would break callers or add needless complexity."),
]

JUDGE = Agent("Tech Lead Judge",
              "You are an impartial tech lead. You weigh the reviewers' arguments, keep what is "
              "well-supported, drop what is over-engineered, and write the final corrected code.", 0.2)


def _numbered(code: str) -> str:
    return "\n".join(f"{i:>2}| {l}" for i, l in enumerate(code.splitlines(), 1))


def _transcript(history: list[list[tuple[str, str]]]) -> str:
    out = []
    for r, turns in enumerate(history):
        out.append(f"--- Round {r + 1} ---")
        out += [f"[{who}]\n{text}" for who, text in turns]
    return "\n\n".join(out)


def run(task_key: str, trace: Trace | None = None, rounds: int = 2) -> dict:
    trace = trace or Trace()
    task = load_task(task_key)
    code = task.starter[task.entry]

    trace.add("Pull request", task.spec, agent="author")
    trace.add(task.entry, code, kind="code", lang="python", agent="author")
    before = run_tests(task.starter, task.tests)
    trace.add(f"Hidden test suite on the PR as submitted: {before.summary()}", before.output,
              kind="tests", ok=before.ok, agent="Sandbox")

    history: list[list[tuple[str, str]]] = []
    for r in range(rounds):
        trace.add("Opening statements" if r == 0 else f"Rebuttal round {r}", kind="step")
        turns = []
        for a in DEBATERS:
            if r == 0:
                prompt = (f"{task.spec}\n\nCode under review:\n```python\n{_numbered(code)}\n```\n\n"
                          "Give your review: at most 4 issues, each with severity (blocker/major/minor), "
                          "the line number, why it matters, and a concrete fix. End with your position: "
                          "APPROVE or REQUEST_CHANGES. Max 200 words.")
            else:
                prompt = (f"{task.spec}\n\nCode under review:\n```python\n{_numbered(code)}\n```\n\n"
                          f"The debate so far:\n{_transcript(history)}\n\n"
                          "Your turn. Name at least one other reviewer and say whether you accept or reject "
                          "their point and why. Revise your own list if they convinced you. Call out any "
                          "proposed fix that would break existing callers. End with your position. Max 180 words.")
            text = a.ask(prompt).strip()
            turns.append((a.name, text))
            trace.add(a.name, text, agent=a.name)
        history.append(turns)

    trace.add("Judge", kind="step")
    raw = generate(
        f"{task.spec}\n\nOriginal code:\n```python\n{code}```\n\nFull debate:\n{_transcript(history)}\n\n"
        "Write the verdict using EXACTLY these markdown sections:\n"
        "## Verdict\nAPPROVE or REQUEST_CHANGES (judging the PR AS SUBMITTED)\n## Agreed issues\n- bullets\n"
        "## Open disagreements\n- bullets (and how you resolved each)\n## Rationale\nshort\n"
        "## Patched code\nthe COMPLETE corrected file in one ```python block. Keep existing public "
        "behaviour and return shapes. Before finishing, re-read every docstring in the original code and make "
        "sure the patched code actually does what each docstring promises.",
        system=JUDGE.persona, temperature=JUDGE.temperature)
    sec = extract_sections(raw)
    trace.add("Verdict: " + (sec.get("verdict", "?").split("\n")[0]), 
              f"**Agreed issues**\n{sec.get('agreed issues', '')}\n\n**Open disagreements**\n"
              f"{sec.get('open disagreements', '')}\n\n**Rationale**\n{sec.get('rationale', '')}", agent=JUDGE.name)

    patched = extract_code(sec.get("patched code", raw))
    trace.add("Judge's patched code", patched, kind="code", lang="python", agent=JUDGE.name)
    after = run_tests({**task.starter, task.entry: patched}, task.tests)
    trace.add(f"Sandbox: {after.summary()}", after.output, kind="tests", ok=after.ok, agent="Sandbox")

    return {
        "solved": after.ok,
        "headline": f"PR as submitted: {before.summary()}  →  after debate: {after.summary()}",
        "report": after,
        "files": {task.entry: patched},
        "stats": {"rounds": rounds, "llm_calls": rounds * len(DEBATERS) + 1},
    }


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "review_orders")
