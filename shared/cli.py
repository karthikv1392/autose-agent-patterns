"""Tiny CLI wrapper so every pattern can be run without the UI:

    python -m patterns.s01_self_reflection.agent [task_key]
"""

import sys

from shared.trace import Trace, print_event


def run_cli(run, default_task: str, **options) -> None:
    task_key = sys.argv[1] if len(sys.argv) > 1 else default_task
    result = run(task_key, trace=Trace(on_event=print_event), **options)
    print("\n" + "#" * 70)
    print(("✅ " if result["solved"] else "❌ ") + result["headline"])
