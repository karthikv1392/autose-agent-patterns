"""Control-flow tests for the Skill Repository, Generator-Critic and Human Approval patterns.

The LLM is replaced by a scripted fake, so these run without Ollama. They check what the patterns
promise: which agent sees what, when the loop stops, and which solutions get saved. The tests are
still the real sandbox run on real task data.

Run:  python -m unittest discover -s tests
"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from patterns.m05_skill_repository import agent as skills
from patterns.m05_skill_repository.skill_store import SkillStore
from patterns.m06_generator_critic import agent as loop
from patterns.m07_human_approval import agent as approval
from shared.tasks import load_reference, load_task


def reference_code(key: str) -> str:
    return next(iter(load_reference(key).values()))


def code_reply(code: str, extra: str = "") -> str:
    return f"```python\n{code}```\n{extra}"


def critique_json(score: int, must_fix: list[str]) -> str:
    sev = "must_fix" if must_fix else "ok"
    crit = {c: {"score": score, "feedback": "f", "severity": sev}
            for c in ("correctness", "security", "efficiency", "readability", "error_handling")}
    return json.dumps({"criteria_scores": crit, "overall_score": score, "overall_feedback": "fb", "must_fix": must_fix})


class FakeLLM:
    """Answers by looking at the prompt. Records every prompt for later assertions."""

    def __init__(self, handler):
        self.handler, self.prompts = handler, []

    def __call__(self, prompt, system=None, temperature=None, stop=None):
        self.prompts.append(prompt)
        return self.handler(prompt, len(self.prompts))


class GeneratorCriticTests(unittest.TestCase):
    def run_loop(self, handler, **kw):
        fake = FakeLLM(handler)
        with mock.patch("shared.agent.generate", fake):
            return loop.run("parse_duration", **kw), fake

    def test_stops_when_the_gate_passes_and_feeds_must_fix_back(self):
        good, bad = reference_code("parse_duration"), "def parse_duration(text):\n    return 0\n"

        def handler(prompt, n):
            if "reviewing a Python draft" in prompt:
                return critique_json(4, ["correctness: wrong result"]) if "return 0" in prompt else critique_json(8, [])
            return code_reply(bad if "MUST-FIX" not in prompt else good, "Rationale: ok")

        result, fake = self.run_loop(handler, max_iterations=4)
        self.assertEqual(result["stats"]["iterations"], 2)
        self.assertTrue(result["stats"]["critic_passed"])
        self.assertTrue(result["solved"])
        self.assertEqual((result["stats"]["initial_score"], result["stats"]["final_score"]), (4, 8))
        refine_prompt = next(p for p in fake.prompts if "MUST-FIX" in p)
        self.assertIn("correctness: wrong result", refine_prompt)
        self.assertNotIn("test_suite", refine_prompt)              # the generator never sees the tests

    def test_stops_at_the_iteration_limit(self):
        def handler(prompt, n):
            if "reviewing a Python draft" in prompt:
                return critique_json(3, ["correctness: still wrong"])
            return code_reply("def parse_duration(text):\n    return 0\n")

        result, _ = self.run_loop(handler, max_iterations=2)
        self.assertEqual(result["stats"]["iterations"], 2)
        self.assertFalse(result["stats"]["critic_passed"])
        self.assertFalse(result["solved"])

    def test_critic_can_pass_code_that_fails_the_tests(self):
        def handler(prompt, n):
            if "reviewing a Python draft" in prompt:
                return critique_json(9, [])
            return code_reply("def parse_duration(text):\n    return 0\n")

        result, _ = self.run_loop(handler)
        self.assertTrue(result["stats"]["critic_passed"])
        self.assertFalse(result["solved"])                          # critic opinion is not ground truth

    def test_unparseable_critique_does_not_pass(self):
        def handler(prompt, n):
            return "no json here" if "reviewing a Python draft" in prompt else code_reply(reference_code("parse_duration"))

        result, _ = self.run_loop(handler, max_iterations=1)
        self.assertFalse(result["stats"]["critic_passed"])


class SkillRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.store = SkillStore(path=Path(self.dir.name) / "lib.json")

    def run_pattern(self, key, handler, **kw):
        fake = FakeLLM(handler)
        with mock.patch("shared.agent.generate", fake):
            return skills.run(key, store=self.store, **kw), fake

    @staticmethod
    def meta(name="Strict token parser", reusable=True) -> str:
        return ("```json\n" + json.dumps({"approach": "from_scratch", "skills_used": [], "is_reusable": reusable,
                                           "name": name, "description": "Parses strict tokens.",
                                           "tags": ["parser", "strict"]}) + "\n```\n")

    def test_seed_library_is_copied_and_the_seed_is_untouched(self):
        self.assertEqual(self.store.size(), 4)
        self.assertTrue((Path(self.dir.name) / "lib.json").exists())

    def test_solves_saves_then_reuses_the_skill_in_a_later_run(self):
        def first(prompt, n):
            if "Skill library" in prompt:
                return json.dumps({"relevant_skill_ids": [], "reasoning": "nothing fits"})
            return self.meta() + code_reply(reference_code("parse_duration"))

        result, _ = self.run_pattern("parse_duration", first)
        self.assertTrue(result["solved"])
        self.assertEqual((result["stats"]["skills_before"], result["stats"]["skills_after"]), (4, 5))

        def second(prompt, n):
            if "Skill library" in prompt:
                skill_id = re.search(r"id=(\S+)\n\s+Name: Strict token parser", prompt).group(1)
                return json.dumps({"relevant_skill_ids": [skill_id], "reasoning": "same kind of parser"})
            return self.meta("Roman numeral parser").replace("from_scratch", "adapted_from_skill") + code_reply(reference_code("roman_to_int"))

        result, fake = self.run_pattern("roman_to_int", second)
        self.assertEqual(result["stats"]["retrieved"], ["Strict token parser"])
        solve_prompt = fake.prompts[-1]
        self.assertIn("Retrieved skill: Strict token parser", solve_prompt)
        self.assertIn("def parse_duration", solve_prompt)             # the full solution is loaded only now
        search_prompt = fake.prompts[0]
        self.assertNotIn("def parse_duration", search_prompt)         # the search sees summaries, not code
        self.assertEqual(next(s for s in self.store.all_skills() if s.name == "Strict token parser").use_count, 1)
        self.assertEqual(self.store.size(), 6)

    def test_failing_solution_is_not_saved(self):
        def handler(prompt, n):
            if "Skill library" in prompt:
                return json.dumps({"relevant_skill_ids": []})
            return self.meta() + code_reply("def parse_duration(text):\n    return 0\n")

        result, _ = self.run_pattern("parse_duration", handler)
        self.assertFalse(result["solved"])
        self.assertEqual(self.store.size(), 4)

    def test_not_reusable_solution_is_not_saved(self):
        def handler(prompt, n):
            if "Skill library" in prompt:
                return json.dumps({"relevant_skill_ids": []})
            return self.meta(reusable=False) + code_reply(reference_code("parse_duration"))

        result, _ = self.run_pattern("parse_duration", handler)
        self.assertTrue(result["solved"])
        self.assertEqual(self.store.size(), 4)

    def test_empty_library_solves_from_scratch_without_a_search_call(self):
        empty = SkillStore(path=Path(self.dir.name) / "empty.json", seed=Path(self.dir.name) / "none.json")
        self.assertEqual(empty.size(), 0)
        fake = FakeLLM(lambda p, n: self.meta() + code_reply(reference_code("parse_duration")))
        with mock.patch("shared.agent.generate", fake):
            result = skills.run("parse_duration", store=empty)
        self.assertEqual(len(fake.prompts), 1)
        self.assertTrue(result["solved"])


class HumanApprovalTests(unittest.TestCase):
    """pager_bugs: a routine fix, a risky rename of a public function, a simulated deploy, a test run."""

    ACTIONS = [
        {"action": "Read pager.py", "type": "read", "target": "pager.py", "expected_outcome": "understand"},
        {"action": "Fix the off-by-one bugs in pager.py", "type": "edit", "target": "pager.py", "expected_outcome": "bugs fixed"},
        {"action": "Rename page_count to count_pages in pager.py", "type": "edit", "target": "pager.py", "expected_outcome": "new name"},
        {"action": "Deploy the fix to production", "type": "deploy", "target": "production", "expected_outcome": "live"},
        {"action": "Run the test suite", "type": "test", "target": "test_suite.py", "expected_outcome": "green"},
    ]
    SCORES = {"Read": 1, "Fix": 5, "Rename": 8, "Deploy": 9, "Run": 2}

    def handler(self, prompt, n):
        if "discrete, sequential actions" in prompt:
            return json.dumps({"summary": "fix the pager", "actions": self.ACTIONS})
        if "Evaluate this action" in prompt:
            word = re.search(r"Action : (\w+)", prompt).group(1)
            return json.dumps({"risk_score": self.SCORES[word], "risk_level": "low", "reasoning": "r",
                               "reversibility": "hard to reverse", "impact_scope": "system-wide"})
        if "Make this change" in prompt:
            good = reference_code("pager_bugs")
            return code_reply(good.replace("def page_count", "def count_pages") if "Rename" in prompt else good)
        raise AssertionError(prompt[:80])

    def run_pattern(self, decide):
        fake = FakeLLM(self.handler)
        with mock.patch("shared.agent.generate", fake):
            return approval.run("pager_bugs", decide=decide), fake

    def test_rejecting_the_risky_actions_keeps_the_tests_green(self):
        asked = []

        def reject(action):
            asked.append(action["index"])
            return {"status": "rejected", "approver": "sam", "notes": "breaks callers"}

        result, _ = self.run_pattern(reject)
        self.assertEqual(asked, [3, 4])                               # only the high-risk actions are put to a person
        self.assertEqual(result["stats"], {"auto": 3, "approved": 0, "rejected": 2, "simulated": 0})
        self.assertTrue(result["solved"])
        self.assertIn("def page_count", result["files"]["pager.py"])
        events = [(r["action_index"], r["event"]) for r in result["audit"]]
        self.assertIn((3, "rejected"), events)
        self.assertIn((3, "skipped"), events)
        self.assertNotIn((3, "executed"), events)

    def test_approving_the_risky_rename_breaks_the_tests_and_the_deploy_is_simulated(self):
        result, _ = self.run_pattern(lambda a: {"status": "approved", "approver": "sam", "notes": ""})
        self.assertEqual(result["stats"]["approved"], 2)
        self.assertEqual(result["stats"]["simulated"], 1)             # the deploy
        self.assertFalse(result["solved"])                            # the human approved a breaking change
        self.assertTrue(any(r["actor"] == "sam" and r["event"] == "approved" for r in result["audit"]))

    def test_a_missing_decision_counts_as_rejected(self):
        fake = FakeLLM(self.handler)
        with mock.patch("shared.agent.generate", fake):
            state = approval.plan("pager_bugs")
            result = approval.execute(state, {})
        self.assertEqual(result["stats"]["rejected"], 2)
        self.assertTrue(all(r["actor"] == "system" for r in result["audit"] if r["event"] == "rejected"))

    def test_the_level_comes_from_the_score_not_from_the_models_label(self):
        fake = FakeLLM(self.handler)                                  # the fake always claims "low"
        with mock.patch("shared.agent.generate", fake):
            state = approval.plan("pager_bugs")
        levels = {a["index"]: a["risk_level"] for a in state["actions"]}
        self.assertEqual(levels, {1: "low", 2: "medium", 3: "high", 4: "high", 5: "low"})
        self.assertEqual([e.action_index for e in state["audit"].events("notified")], [3, 4])

    def test_a_read_of_several_files_is_real_and_a_read_of_a_missing_file_is_simulated(self):
        from patterns.m07_human_approval.executor import execute_action
        files = {"a.py": "x = 1\n", "b.py": "y = 2\n"}
        multi = execute_action({"type": "read", "target": "a.py, b.py", "action": "r", "expected_outcome": ""}, files, "", "")
        missing = execute_action({"type": "read", "target": "test_suite.py", "action": "r", "expected_outcome": ""}, files, "", "")
        self.assertFalse(multi["simulated"])
        self.assertTrue(missing["simulated"])

    def test_an_unparseable_plan_falls_back_to_read_edit_test(self):
        def handler(prompt, n):
            if "discrete, sequential actions" in prompt:
                return "I cannot produce JSON"
            return json.dumps({"risk_score": 2})
        with mock.patch("shared.agent.generate", FakeLLM(handler)):
            state = approval.plan("pager_bugs")
        self.assertEqual([a["type"] for a in state["actions"]], ["read", "edit", "test"])

    def test_audit_sequence_numbers_are_monotonic(self):
        result, _ = self.run_pattern(lambda a: {"status": "rejected", "approver": "x", "notes": ""})
        seqs = [r["seq"] for r in result["audit"]]
        self.assertEqual(seqs, sorted(seqs))
        self.assertEqual(len(seqs), len(set(seqs)))


if __name__ == "__main__":
    unittest.main()
