"""Spawner — looks at the codebase and INVENTS the sub-agents needed for it.

Nothing about the sub-agents is hard-coded: how many there are, their names,
personas and instructions all come from the Spawner's LLM output, shaped by what
it sees in the repo (e.g. a module full of print() calls gets a logging specialist).
"""

import ast
import json
import re

from shared.llm import generate

SYSTEM = ("You are an engineering manager who splits refactoring work across specialist engineers. "
          "You look at a codebase and decide who is needed.")


def describe_repo(files: dict[str, str]) -> str:
    lines = []
    for name, src in sorted(files.items()):
        tree = ast.parse(src)
        defs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        lines.append(f"- {name}: {len(src.splitlines())} lines; defines {', '.join(defs)}; "
                     f"print() calls: {src.count('print(')}")
    return "\n".join(lines)


def _fallback(files: dict[str, str]) -> list[dict]:
    return [{"name": f"{f.removesuffix('.py').title()} Modernizer", "file": f,
             "persona": "You are a careful Python engineer who modernises code without changing behaviour.",
             "instructions": "Apply the full task to this file."} for f in sorted(files)]


def spawn(task_spec: str, files: dict[str, str], max_agents: int) -> dict:
    prompt = (
        f"Task for the whole codebase:\n{task_spec}\n\nCodebase:\n{describe_repo(files)}\n\n"
        f"Create between 2 and {max_agents} specialist sub-agents. Each owns exactly ONE file from the "
        "list and every file must be owned by exactly one sub-agent. For each give:\n"
        '  "name"         a specific title, e.g. "Logging Migration Specialist (inventory.py)"\n'
        '  "file"         the file it owns\n'
        '  "persona"      2 sentences: its expertise and working style\n'
        '  "instructions" what is special about THIS file that it must watch for\n'
        'Return JSON only: {"strategy": "one sentence", "subagents": [{...}]}'
    )
    raw = generate(prompt, system=SYSTEM, temperature=0.3)
    try:
        m = re.search(r"\{[\s\S]*\}", raw)
        data = json.loads(m.group(0))
        specs, seen = [], set()
        for s in data["subagents"]:
            if s.get("file") in files and s["file"] not in seen and s.get("name"):
                seen.add(s["file"])
                specs.append({k: str(s.get(k, "")) for k in ("name", "file", "persona", "instructions")})
        strategy = str(data.get("strategy", ""))
    except Exception:
        specs, strategy = [], ""
    # Safety net: any file the Spawner forgot still gets a worker.
    covered = {s["file"] for s in specs}
    specs += [s for s in _fallback({f: files[f] for f in files if f not in covered})]
    return {"strategy": strategy or "One specialist per module.", "specs": specs}
