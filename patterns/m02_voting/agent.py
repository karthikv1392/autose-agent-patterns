"""Multi-agent pattern 2 — Voting (behavioural consensus over code candidates).

   spec ─► Candidate 1 ─┐
           Candidate 2 ─┤   run every candidate on the same probe inputs
           Candidate 3 ─┼─► group candidates whose OUTPUTS agree ─► biggest group wins
           Candidate N ─┘            (no tests needed to pick the winner)

Why it matters for software engineering
---------------------------------------
Several independent attempts are unlikely to make the *same* mistake. Rather than
asking an LLM which solution "looks" best, we execute all of them on probe inputs
and vote on behaviour: the answer most candidates agree on wins. This is the idea
behind self-consistency and CodeT-style selection, and it works when you have a
spec but no tests yet. We then check the winner against the hidden tests to see
whether the vote was right.

Limit worth teaching: voting only helps when candidates' mistakes are INDEPENDENT.
On merge_intervals most candidates agree and are right. On roman_to_int the candidates
share the same blind spot (strict canonical form), so the majority can be confidently
wrong — agreement is not correctness.

(Existing repo analogue: Multi_Agent_Pattern/patterns/p01_voting_cooperation.)
"""

import concurrent.futures
from collections import defaultdict

from shared.agent import Agent
from shared.codeutil import extract_code
from shared.sandbox import run_script, run_tests
from shared.tasks import load_task
from shared.trace import Trace

STYLES = [
    ("Straightforward", "Write the most straightforward, readable solution."),
    ("Defensive", "Be defensive: validate inputs and handle every edge case explicitly."),
    ("Pythonic", "Prefer concise, idiomatic Python and the standard library."),
    ("Rule-by-rule", "Go through the spec rule by rule and implement each rule as an explicit check."),
    ("Test-first", "Think like a test-driven developer: imagine the unit tests first, then implement."),
    ("Regex-minded", "Use regular expressions or well-known stdlib helpers wherever they fit."),
    ("Performance", "Optimise for clarity and efficiency, but never at the cost of correctness."),
]

BASE = ("You are a senior Python engineer. Standard library only. Reply with ONE ```python block "
        "containing the complete file and nothing else (no tests, no usage examples). ")


def _probe_script(probes: list[str]) -> str:
    return (
        f"probes = {probes!r}\n"
        "try:\n    import solution\nexcept Exception as e:\n"
        "    print('IMPORT_ERROR:' + type(e).__name__); raise SystemExit(0)\n"
        "ns = dict(vars(solution))\n"
        "for p in probes:\n"
        "    try: print(repr(eval(p, ns)))\n"
        "    except Exception as e: print('EXC:' + type(e).__name__)\n"
    )


def run(task_key: str, trace: Trace | None = None, num_candidates: int = 5) -> dict:
    trace = trace or Trace()
    task = load_task(task_key)
    n = max(2, min(num_candidates, len(STYLES)))
    agents = [Agent(f"Candidate {i + 1} · {name}", BASE + hint, temperature=0.9)
              for i, (name, hint) in enumerate(STYLES[:n])]

    trace.add("Task", task.spec, agent="user")
    trace.add(f"1 · {n} independent candidates", kind="step")
    prompt = f"Write the complete `{task.entry}` for this specification.\n\n{task.spec}"
    # LLM calls are independent, so they can run concurrently. Trace events are added afterwards,
    # on the main thread (Streamlit is not thread-safe).
    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
        codes = [extract_code(r) for r in pool.map(lambda a: a.ask(prompt), agents)]
    for a, c in zip(agents, codes):
        trace.add(a.name, c, kind="code", lang="python", agent=a.name)

    trace.add("2 · Run every candidate on the same probe inputs", kind="step")
    signatures = []
    script = _probe_script(task.probes)
    for c in codes:
        res = run_script({task.entry: c}, script)
        signatures.append(res.stdout if res.ok else f"CRASH:{res.stderr[-80:]}")

    groups: dict[str, list[int]] = defaultdict(list)
    for i, sig in enumerate(signatures):
        groups[sig].append(i)
    ranked = sorted(groups.values(), key=lambda idx: (-len(idx), idx[0]))
    group_of = {i: g for g, idx in enumerate(ranked) for i in idx}
    trace.add("Probe outputs", kind="table", agent="Voter", data=[
        {"probe": p, **{f"C{i + 1}": (sig.splitlines()[k] if k < len(sig.splitlines()) else "-")
                        for i, sig in enumerate(signatures)}}
        for k, p in enumerate(task.probes)])

    winner = ranked[0][0]
    trace.add("3 · Vote", kind="step")
    trace.add("Behaviour groups", f"{len(ranked)} distinct behaviour(s). Largest group: "
              f"{[f'C{i + 1}' for i in ranked[0]]} ({len(ranked[0])}/{n} votes) → winner {agents[winner].name}",
              agent="Voter")

    trace.add("4 · Check against the hidden tests (ground truth, not used for voting)", kind="step")
    reports = [run_tests({task.entry: c}, task.tests) for c in codes]
    trace.add("Scoreboard", kind="table", agent="Sandbox", data=[
        {"candidate": agents[i].name, "behaviour group": f"G{group_of[i] + 1}",
         "votes": len(ranked[group_of[i]]), "tests": reports[i].summary(),
         "winner": "🏆" if i == winner else ""} for i in range(n)])
    trace.add(f"Winner: {reports[winner].summary()}", reports[winner].output, kind="tests",
              ok=reports[winner].ok, agent="Sandbox")

    avg = sum(r.pass_rate for r in reports) / n
    best = max(r.pass_rate for r in reports)
    return {
        "solved": reports[winner].ok,
        "headline": (f"Voted winner: {reports[winner].summary()} · average single candidate: "
                     f"{avg:.0%} · best-of-{n} oracle: {best:.0%}"),
        "report": reports[winner],
        "files": {task.entry: codes[winner]},
        "stats": {"avg_candidate_pass_rate": avg, "winner_pass_rate": reports[winner].pass_rate,
                  "behaviour_groups": len(ranked)},
    }


if __name__ == "__main__":
    from shared.cli import run_cli
    run_cli(run, "merge_intervals")
