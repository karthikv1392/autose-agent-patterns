"""Control-flow tests for the Skill Repository and Generator-Critic patterns.

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


if __name__ == "__main__":
    unittest.main()
