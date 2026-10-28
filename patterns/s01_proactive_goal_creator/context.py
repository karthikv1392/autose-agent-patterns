"""Context gatherers for the Proactive Goal Creator (software-engineering flavour).

A human engineer handed "the pager is broken" would not start typing a fix. They
would look around first: what is in the repo, what do the tests say, which
Python is this? These functions do that looking-around *automatically*, before
the LLM is ever called. That is what "proactive" means here.
"""

import ast
import platform
import sys

from shared.sandbox import run_tests


def gather_env_context() -> str:
    return (
        f"- Python: {sys.version.split()[0]}\n"
        f"- Platform: {platform.system()} {platform.release()}\n"
        "- Constraint: standard library only, unittest for tests"
    )


def gather_repo_map(files: dict[str, str]) -> str:
    """File list plus a one-line outline (classes / functions) for each file."""
    lines = []
    for name, src in sorted(files.items()):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            lines.append(f"- {name}: (does not parse)")
            continue
        symbols = [
            f"{'class' if isinstance(n, ast.ClassDef) else 'def'} {n.name}"
            for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))
        ]
        lines.append(f"- {name} ({len(src.splitlines())} lines): {', '.join(symbols) or '-'}")
    return "\n".join(lines)


def gather_test_status(files: dict[str, str], tests: str) -> tuple[str, str]:
    """Run the test suite NOW, so the agent starts from facts: (summary, raw output)."""
    report = run_tests(files, tests)
    return report.summary(), report.output


def gather_source(files: dict[str, str]) -> str:
    return "\n\n".join(f"### {name}\n```python\n{src}```" for name, src in sorted(files.items()))
