# AutoSE Agent Patterns

Agentic design patterns applied to **autonomous software engineering** (code generation, bug fixing,
code review, large refactors). It is a self-contained companion to the generic
[`Agentic_Patterns`](../Agentic_Patterns) project: same teaching style, same local-Ollama setup, but
every demo is a software-engineering task whose result is **checked by running real tests**.

> Nothing in `Agentic_Patterns` is modified or imported by this project.

## Patterns

| # | Pattern | SE scenario | What the demo shows |
|---|---|---|---|
| S1 | **Proactive Goal Creator** | Vague bug report ("the pager is broken") | Agent first gathers env, repo map, a fresh test run and sources, then asks the LLM. Compared with goal-only. |
| S2 | **Incremental Tool Agent** | Bug fix with developer tools (`read_file`, `search_code`, `run_tests`, `list_files`) | Three small LLM rounds: analyse → plan + choose tool → exact JSON parameters; then run the tool and write the fix. |
| S3 | **Self-Reflection** | Implement a spec-heavy function | Plan → critique the plan → implement → test → diagnose failures → revise. |
| M1 | **Debate** | Code review of a pull request | Security / Correctness / Maintainer argue; a judge writes a patched file that is run against hidden tests. |
| M2 | **Voting** | Pick the best of N generated solutions | Candidates are executed on probe inputs; the behaviour most agree on wins — no tests needed to choose. |
| M3 | **Sub-agent Spawning** | Modernise a 4-module legacy codebase | A spawner invents one specialist per module; they run in parallel; the existing test suite + static metrics verify. |
| M4 | **Swarm** | Build a class until the suite is green | Coder → Tester → Debugger → Reviewer hand work to each other; the path emerges at runtime. |
| M5 | **Skill Repository** | Reuse solutions across sessions | The agent searches a persistent library of earlier solutions, adapts what fits, and saves a new skill only when its tests pass. Run `parse_duration`, then `roman_to_int`. |
| M6 | **Generator-Critic Loop** | Draft, review and revise code | A generator drafts, a critic scores five criteria and lists must-fix issues, and the draft is revised until the gate passes. Hidden tests run on every draft but are never shown to the generator. |

Each pattern's `agent.py` opens with an ASCII diagram and a "why it matters for software engineering"
note — the Streamlit app shows that docstring as the explanation.

## Layout

```
AutoSE_Agent_Patterns/
├── app.py                  Streamlit UI (generic: renders any pattern's trace)
├── run.sh                  creates .venv and launches the app
├── patterns/
│   ├── registry.py         the list of patterns, tasks and options
│   ├── s01_proactive_goal_creator/   context.py · agent.py
│   ├── s02_incremental_tool_agent/   tools.py · agent.py
│   ├── s03_self_reflection/          planner.py · reflector.py · executor.py · agent.py
│   ├── m01_debate/ · m02_voting/ · m03_subagent_spawning/ · m04_swarm/
│   ├── m05_skill_repository/         skill_store.py · skill_agent.py · agent.py
│   ├── m06_generator_critic/         generator.py · critic.py · agent.py
├── shared/
│   ├── llm.py              Ollama client (model via AUTOSE_MODEL)
│   ├── sandbox.py          runs generated code + unittest in a temp dir (ground truth)
│   ├── tasks.py            loads task_data/<task>/
│   ├── trace.py            UI-agnostic event log every pattern writes to
│   └── agent.py · codeutil.py · diffutil.py · cli.py
├── task_data/              one folder per task: spec.md, starter/, test_suite.py, reference/
└── tests/test_tasks.py     checks every task: starter fails, reference passes
```

## Run

Prerequisites: Python 3.10+, [Ollama](https://ollama.com) running locally with a model pulled
(`ollama pull gemma4`).

```bash
./run.sh                                   # Streamlit UI on http://localhost:8503
# or without the UI:
python -m patterns.s03_self_reflection.agent parse_duration
python -m patterns.m04_swarm.agent lru_cache
```

Use another model: `AUTOSE_MODEL=qwen3 ./run.sh` (or pick it in the sidebar). Hidden "thinking" is off by
default for speed; set `AUTOSE_THINK=1` to enable it for reasoning models.

Validate the task data and the loop logic any time: `python -m unittest discover -s tests`. The pattern tests use a scripted fake LLM, so they need no Ollama.

## How to read results

* Every outcome is decided by **executing tests**, not by an LLM's opinion. The pass counts in the UI
  are real.
* Local models are non-deterministic: re-running can change the numbers. That variance is itself a
  teaching point (compare runs, change the model, change the number of candidates).
* **Voting caveat:** on `merge_intervals` the candidates agree and are right. On `roman_to_int` /
  `parse_duration` they often share the same blind spot, so the majority can be confidently wrong.
  Agreement is not correctness — voting only helps when errors are independent.

## The skill library

The Skill Repository keeps its library in `patterns/m05_skill_repository/skill_library.json`, created from `skill_library.seed.json` on first use and ignored by git. Delete it to start over.

## Safety note

`shared/sandbox.py` runs model-written code in a separate process with a timeout inside a temp
directory. That is fine for a classroom demo, but it is **not** a security sandbox. Use containers
before running untrusted models or code.

## Adding a task

Create `task_data/<name>/` with `task.json` (`title`, `kind`, `entry`, `summary`), `spec.md`,
`test_suite.py`, optional `starter/`, `probes.txt` and `reference/`, then list it under a pattern in
`patterns/registry.py`. `tests/test_tasks.py` will verify it.

## Learning website

`website/` is a static step-by-step guide to the nine patterns (Vite + React). Each pattern has an interactive
diagram that walks through what happens at every step.

```bash
./run.sh site        # installs dependencies on first run, opens http://localhost:5173
./run.sh both        # website and Streamlit demo together
```

The site is deployed to GitHub Pages by `.github/workflows/pages.yml` on every push to `main` that touches `website/`.
To build it by hand, run `npm run build` inside `website/` (output in `website/dist`).
