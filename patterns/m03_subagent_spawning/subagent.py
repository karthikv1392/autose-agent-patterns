"""SubAgent — instantiated at runtime from a spec the Spawner wrote.

Context isolation is the point: each sub-agent sees ONLY its own file plus the
public signatures of the other modules (read-only). Small, focused context means
fewer mistakes and lets all sub-agents run in parallel.
"""

import ast
import time

from shared.agent import Agent
from shared.codeutil import extract_code


def api_outline(files: dict[str, str], exclude: str) -> str:
    out = []
    for name, src in sorted(files.items()):
        if name == exclude:
            continue
        for n in ast.parse(src).body:
            if isinstance(n, ast.FunctionDef):
                out.append(f"{name}: def {n.name}({', '.join(a.arg for a in n.args.args)})")
            elif isinstance(n, ast.ClassDef):
                out.append(f"{name}: class {n.name}")
    return "\n".join(out) or "(none)"


def work(spec: dict, task_spec: str, files: dict[str, str]) -> dict:
    """Run one sub-agent on its file. Returns the new source or an error."""
    agent = Agent(spec["name"],
                  spec["persona"] + " Reply with ONE ```python block containing the COMPLETE updated file "
                  "and nothing else.", temperature=0.2)
    prompt = (
        f"Overall task:\n{task_spec}\n\nYou own `{spec['file']}`. Special notes: {spec['instructions']}\n\n"
        f"Other modules (read-only, for reference; do NOT change how they are imported or called):\n"
        f"{api_outline(files, spec['file'])}\n\n"
        f"Current `{spec['file']}`:\n```python\n{files[spec['file']]}```\n\n"
        "Return the complete updated file. Keep every public name, signature and behaviour identical."
    )
    start = time.time()
    code = extract_code(agent.ask(prompt))
    error = None
    try:
        ast.parse(code)
    except SyntaxError as e:
        error = f"SyntaxError: {e.msg} (line {e.lineno}) — original kept"
    return {"spec": spec, "code": code, "error": error, "seconds": round(time.time() - start, 1)}
