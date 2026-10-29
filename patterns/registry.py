"""Pattern registry — the single list the UI (and docs) are built from.

Adding a pattern = write patterns/<id>/agent.py with `run(task_key, trace, **options)`
and add one entry here.
"""

import importlib

PATTERNS = [
    {
        "id": "s01_proactive_goal_creator", "group": "Single agent",
        "title": "Proactive Goal Creator",
        "tagline": "Gather repo, environment and test context BEFORE asking the LLM to fix a vague bug report.",
        "tasks": ["pager_bugs", "cart_bugs"], "options": [],
        "original": "Single_Agent_Pattern/patterns/p02_proactive_goal_creator",
    },
    {
        "id": "s02_incremental_tool_agent", "group": "Single agent",
        "title": "Incremental Tool Agent",
        "tagline": "Analyse → plan & choose a developer tool → exact parameters → run it → write the fix.",
        "tasks": ["pager_bugs", "cart_bugs"], "options": [],
        "original": "Single_Agent_Pattern/patterns/p06_incremental_tool_agent",
    },
    {
        "id": "s03_self_reflection", "group": "Single agent",
        "title": "Self-Reflection",
        "tagline": "Plan → critique the plan → implement → test → diagnose failures → revise.",
        "tasks": ["parse_duration", "roman_to_int"],
        "options": [{"key": "max_revisions", "label": "Max post-test revisions", "min": 0, "max": 4, "default": 3}],
        "original": "Single_Agent_Pattern/patterns/p09_self_reflection",
    },
    {
        "id": "m01_debate", "group": "Multi agent",
        "title": "Debate",
        "tagline": "Security, correctness and maintainer reviewers argue over a PR; a judge patches it.",
        "tasks": ["review_orders"],
        "options": [{"key": "rounds", "label": "Debate rounds", "min": 1, "max": 3, "default": 2}],
        "original": "Multi_Agent_Pattern/patterns/p03_debate_cooperation",
    },
    {
        "id": "m02_voting", "group": "Multi agent",
        "title": "Voting",
        "tagline": "N independent solutions are executed on probe inputs; the behaviour most agree on wins.",
        "tasks": ["merge_intervals", "roman_to_int", "parse_duration"],
        "options": [{"key": "num_candidates", "label": "Candidates", "min": 3, "max": 7, "default": 5}],
        "original": "Multi_Agent_Pattern/patterns/p01_voting_cooperation",
    },
    {
        "id": "m03_subagent_spawning", "group": "Multi agent",
        "title": "Sub-agent Spawning",
        "tagline": "A spawner invents one specialist per module; they refactor in parallel; tests verify.",
        "tasks": ["legacy_shop"],
        "options": [{"key": "max_agents", "label": "Max sub-agents", "min": 2, "max": 4, "default": 4}],
        "original": "Multi_Agent_Pattern/patterns/p10_subagent_spawning",
    },
    {
        "id": "m04_swarm", "group": "Multi agent",
        "title": "Swarm",
        "tagline": "Coder, Tester, Debugger and Reviewer hand work to each other until the suite is green.",
        "tasks": ["lru_cache", "parse_duration"],
        "options": [{"key": "max_hops", "label": "Max hand-offs", "min": 6, "max": 20, "default": 12}],
        "original": "Multi_Agent_Pattern/patterns/p07_swarm",
    },
    {
        "id": "m05_skill_repository", "group": "Multi agent",
        "title": "Skill Repository",
        "tagline": "Search earlier solutions, adapt what fits, and save validated solutions for the next session.",
        "tasks": ["parse_duration", "roman_to_int", "merge_intervals"],
        "options": [{"key": "top_k", "label": "Skills to retrieve", "min": 1, "max": 3, "default": 2}],
        "original": "Multi_Agent_Pattern/patterns/p11_skill_library",
    },
    {
        "id": "m06_generator_critic", "group": "Multi agent",
        "title": "Generator-Critic Loop",
        "tagline": "A generator drafts, a critic scores against criteria, and the draft is revised until a gate passes.",
        "tasks": ["parse_duration", "roman_to_int", "merge_intervals"],
        "options": [{"key": "max_iterations", "label": "Max iterations", "min": 1, "max": 5, "default": 4}],
        "original": "Multi_Agent_Pattern/patterns/p09_generator_critic",
    },
    {
        "id": "m07_human_approval", "group": "Multi agent",
        "title": "Human-in-the-Loop Approval",
        "tagline": "Risky actions wait for a named reviewer; low and medium risk actions run, and everything is audited.",
        "tasks": ["cart_bugs", "pager_bugs", "legacy_shop"],
        "options": [{"key": "num_actions", "label": "Planned actions", "min": 4, "max": 8, "default": 6}],
        "interactive": True,
        "original": "Multi_Agent_Pattern/patterns/p08_human_in_the_loop",
    },
]


def load(pattern_id: str):
    """Import and return the pattern's agent module."""
    return importlib.import_module(f"patterns.{pattern_id}.agent")
