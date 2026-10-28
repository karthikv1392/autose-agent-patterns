"""Sanity checks for the task data — run these before trusting any demo result.

For every task: the starter code must FAIL the tests (otherwise there is nothing
for an agent to do), and the known-good reference must PASS them (otherwise the
tests themselves are wrong). The one exception is the refactor task, whose starter
must already pass (agents must keep it passing).

Run:  python -m unittest discover -s tests
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.sandbox import run_tests
from shared.tasks import list_tasks, load_reference, load_task


class TaskDataTests(unittest.TestCase):
    def test_every_task_is_well_formed(self):
        for key in list_tasks():
            with self.subTest(task=key):
                task = load_task(key)
                self.assertTrue(task.spec)
                self.assertTrue(task.tests)

    def test_starter_fails_and_reference_passes(self):
        for key in list_tasks():
            task = load_task(key)
            with self.subTest(task=key):
                starter_report = run_tests(task.starter, task.tests)
                if task.kind == "refactor":
                    self.assertTrue(starter_report.ok, starter_report.output)
                    continue
                self.assertFalse(starter_report.ok, "starter should not already pass")
                solved = {**task.starter, **load_reference(key)}
                report = run_tests(solved, task.tests)
                self.assertTrue(report.ok, report.output)

    def test_probes_run_against_reference(self):
        from shared.sandbox import run_script
        for key in list_tasks():
            task = load_task(key)
            if not task.probes:
                continue
            with self.subTest(task=key):
                script = "import json, solution\n" \
                         f"for p in {task.probes!r}:\n" \
                         "    try: print(repr(eval(p, vars(solution))))\n" \
                         "    except Exception as e: print('EXC:' + type(e).__name__)\n"
                res = run_script(load_reference(key), script)
                self.assertTrue(res.ok, res.stderr)
                self.assertEqual(len(res.stdout.strip().splitlines()), len(task.probes))


if __name__ == "__main__":
    unittest.main()
