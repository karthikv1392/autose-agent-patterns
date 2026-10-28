import { COPY } from "./copy";

// Diagrams and step structure for every pattern. Diagrams are data: nodes and edges are positioned by hand
// in a 960-wide coordinate space; each step says which of them are active.

export type Kind = "input" | "llm" | "tool" | "data";
export type Side = "t" | "r" | "b" | "l";

export type Node = {
  id: string;
  label: string;          // "\n" breaks lines
  sub?: string;
  kind: Kind;
  x: number; y: number; w: number; h: number;
  runtime?: boolean;      // created at runtime -> dashed outline
};

export type Edge = {
  id: string;
  from: string; to: string;
  fs?: Side; ts?: Side;   // anchor sides (inferred when omitted)
  fOff?: number; tOff?: number;
  mid?: number;           // override for the elbow coordinate
  pts?: [number, number][]; // explicit polyline (absolute), overrides routing
  label?: string;
  dashed?: boolean;
  both?: boolean;         // arrowhead at both ends
  labelLeft?: boolean;    // for vertical edges: put the label left of the line
};

export type Group = { x: number; y: number; w: number; h: number; label: string };
export type Note = { x: number; y: number; text: string; anchor?: "start" | "middle" | "end" };

export type Diagram = {
  height: number;
  nodes: Node[]; edges: Edge[]; groups?: Group[]; notes?: Note[];
};

export type Matrix = {
  caption: string;
  head: string[];           // column headers (first = row label)
  rows: string[][];
  group: number[];          // behaviour group per candidate column (for colouring)
};

type RawStep = {
  title: string;
  actor: "LLM call" | "Plain code" | "Sandbox" | "Input" | "Several LLM calls";
  nodes: string[];
  edges?: string[];
  artifact?: { label: string; kind: "text" | "code" | "tests"; body: string };
  matrix?: Matrix;
  path?: { label: string; steps: string[]; note?: string }[];
};

export type Step = RawStep & { body: string; points?: string[] };

export type Consequence = { attribute: string; effect: "pro" | "con"; text: string };

export type Pattern = {
  id: string;
  code: string;            // S1, M3 ...
  group: "Single agent" | "Multi-agent";
  title: string;
  scenario: string;        // one-line SE scenario
  task: string;            // demo task(s)
  summary: string;
  context: string;
  problem: string;
  solution: string;
  useWhen: string[];
  tradeoff: string;
  consequences: Consequence[];
  llmCalls: string;
  verifiedBy: string;
  diagram: Diagram;
  steps: Step[];
  run: string;
  files: { path: string; what: string }[];
};

type RawPattern = Omit<Pattern, "summary" | "context" | "problem" | "solution" | "useWhen" | "tradeoff" | "consequences" | "steps"> & { steps: RawStep[] };

/* ───────────────────────────── S1 ───────────────────────────── */

const s1: RawPattern = {
  id: "proactive-goal-creator",
  code: "S1",
  group: "Single agent",
  title: "Proactive Goal Creator",
  scenario: "Fix a bug from a vague report",
  task: "pager_bugs, cart_bugs",
  llmCalls: "1 (plus 1 for the goal-only control run in the demo)",
  verifiedBy: "Hidden unit tests run on the patched files",
  diagram: {
    height: 350,
    nodes: [
      { id: "user", label: "Vague bug report", sub: "“the pager is broken”", kind: "input", x: 20, y: 150, w: 170, h: 66 },
      { id: "env", label: "Read environment", sub: "Python, OS, packages", kind: "tool", x: 270, y: 50, w: 200, h: 52 },
      { id: "repo", label: "Map the repository", sub: "files, functions, sizes", kind: "tool", x: 270, y: 120, w: 200, h: 52 },
      { id: "tests", label: "Run the tests", sub: "fresh failing output", kind: "tool", x: 270, y: 190, w: 200, h: 52 },
      { id: "src", label: "Read source files", sub: "the code itself", kind: "tool", x: 270, y: 260, w: 200, h: 52 },
      { id: "prompt", label: "Enriched prompt", sub: "goal + all four\ncontext blocks", kind: "data", x: 545, y: 135, w: 150, h: 82 },
      { id: "llm", label: "LLM", sub: "one call", kind: "llm", x: 770, y: 70, w: 170, h: 62 },
      { id: "sandbox", label: "Sandbox", sub: "run the test suite", kind: "tool", x: 770, y: 250, w: 170, h: 62 },
    ],
    edges: [
      { id: "u-env", from: "user", to: "env" },
      { id: "u-repo", from: "user", to: "repo" },
      { id: "u-tests", from: "user", to: "tests" },
      { id: "u-src", from: "user", to: "src" },
      { id: "env-p", from: "env", to: "prompt" },
      { id: "repo-p", from: "repo", to: "prompt" },
      { id: "tests-p", from: "tests", to: "prompt" },
      { id: "src-p", from: "src", to: "prompt" },
      { id: "p-llm", from: "prompt", to: "llm", fs: "r", ts: "l" },
      { id: "llm-sb", from: "llm", to: "sandbox", label: "patched files" },
      { id: "base", from: "user", to: "llm", dashed: true, label: "control: goal only",
        pts: [[105, 150], [105, 20], [855, 20], [855, 70]] },
    ],
    notes: [{ x: 370, y: 336, text: "plain Python functions, no LLM involved", anchor: "middle" }],
  },
  steps: [
    {
      title: "A vague request arrives",
      actor: "Input",
      nodes: ["user"],
      artifact: { label: "Input", kind: "text", body: "Users say the results pager is broken. Please fix it." },
    },
    {
      title: "Control run: goal only",
      actor: "LLM call",
      nodes: ["user", "llm"],
      edges: ["base"],
      artifact: { label: "Everything the model receives", kind: "text", body: "Users say the results pager is broken. Please fix it.\n\nThe project is a small Python package." },
    },
    {
      title: "Gather four kinds of context",
      actor: "Plain code",
      nodes: ["user", "env", "repo", "tests", "src"],
      edges: ["u-env", "u-repo", "u-tests", "u-src"],
      artifact: {
        label: "Real output of the test-run gatherer on pager_bugs (abbreviated)",
        kind: "tests",
        body: "4/11 tests passed\n...\nFAIL: test_empty_has_one_page\n    self.assertEqual(page_count(0, 10), 1)\nAssertionError: 0 != 1\n\nFAIL: test_first_page\nFAIL: test_last_partial_page\nFAIL: test_invalid_arguments\n...",
      },
    },
    {
      title: "Fold everything into one prompt",
      actor: "Plain code",
      nodes: ["env", "repo", "tests", "src", "prompt"],
      edges: ["env-p", "repo-p", "tests-p", "src-p"],
      artifact: {
        label: "Prompt structure (from the code)",
        kind: "text",
        body: 'The user asked: "Users say the results pager is broken..."\n\n## Environment\n...\n## Repository map\n...\n## Current test results (the bug is whatever makes these fail)\n...\n## Source files\n...\n\nUsing ALL of the context above, fix the code so the tests pass.\nRead each docstring: it states the intended behaviour.',
      },
    },
    {
      title: "One grounded LLM call",
      actor: "LLM call",
      nodes: ["prompt", "llm"],
      edges: ["p-llm"],
      artifact: {
        label: "A correct fix for one of the bugs (reference solution, for illustration)",
        kind: "code",
        body: " def page_count(total_items, per_page):\n-    return total_items // per_page\n+    return max(1, -(-total_items // per_page))",
      },
    },
    {
      title: "The tests decide",
      actor: "Sandbox",
      nodes: ["llm", "sandbox"],
      edges: ["llm-sb"],
    },
  ],
  run: "python -m patterns.s01_proactive_goal_creator.agent pager_bugs",
  files: [
    { path: "patterns/s01_proactive_goal_creator/context.py", what: "the four gatherers" },
    { path: "patterns/s01_proactive_goal_creator/agent.py", what: "control run, enriched prompt, scoring" },
  ],
};

/* ───────────────────────────── S2 ───────────────────────────── */

const s2: RawPattern = {
  id: "incremental-tool-agent",
  code: "S2",
  group: "Single agent",
  title: "Incremental Tool Agent",
  scenario: "Fix a bug using developer tools",
  task: "pager_bugs, cart_bugs",
  llmCalls: "4 (analyse, plan and choose, parameters, synthesis)",
  verifiedBy: "Hidden unit tests run on the patched files",
  diagram: {
    height: 350,
    nodes: [
      { id: "goal", label: "Bug report", sub: "the goal", kind: "input", x: 20, y: 30, w: 170, h: 70 },
      { id: "r1", label: "Round 1\nAnalyse", sub: "what is wrong?", kind: "llm", x: 260, y: 30, w: 170, h: 70 },
      { id: "r2", label: "Round 2\nPlan + choose tool", sub: "no parameters yet", kind: "llm", x: 500, y: 30, w: 190, h: 70 },
      { id: "r3", label: "Round 3\nExact call", sub: "JSON only", kind: "llm", x: 760, y: 30, w: 180, h: 70 },
      { id: "catalogue", label: "Tool catalogue", sub: "read_file · search_code · run_tests · list_files", kind: "data", x: 400, y: 150, w: 400, h: 52 },
      { id: "exec", label: "Execute tool", sub: "plain Python", kind: "tool", x: 760, y: 250, w: 180, h: 70 },
      { id: "synth", label: "Synthesis\nWrite the fix", sub: "full updated files", kind: "llm", x: 500, y: 250, w: 190, h: 70 },
      { id: "tests", label: "Sandbox", sub: "run the test suite", kind: "tool", x: 260, y: 250, w: 170, h: 70 },
    ],
    edges: [
      { id: "g-r1", from: "goal", to: "r1" },
      { id: "r1-r2", from: "r1", to: "r2" },
      { id: "r2-r3", from: "r2", to: "r3" },
      { id: "cat-r2", from: "catalogue", to: "r2", fs: "t", ts: "b", fOff: -90, tOff: 20, dashed: true, label: "descriptions" },
      { id: "cat-r3", from: "catalogue", to: "r3", fs: "t", ts: "b", fOff: 150, tOff: -40, dashed: true },
      { id: "r3-ex", from: "r3", to: "exec", label: "tool + args" },
      { id: "ex-syn", from: "exec", to: "synth", label: "tool output" },
      { id: "syn-t", from: "synth", to: "tests" },
    ],
    notes: [
      { x: 20, y: 130, text: "Each round receives the goal", anchor: "start" },
      { x: 20, y: 146, text: "plus every earlier round.", anchor: "start" },
    ],
  },
  steps: [
    {
      title: "The bug report",
      actor: "Input",
      nodes: ["goal"],
    },
    {
      title: "Round 1: analyse",
      actor: "LLM call",
      nodes: ["goal", "r1"],
      edges: ["g-r1"],
    },
    {
      title: "Round 2: plan and choose a tool",
      actor: "LLM call",
      nodes: ["r1", "r2", "catalogue"],
      edges: ["r1-r2", "cat-r2"],
    },
    {
      title: "Round 3: exact parameters",
      actor: "LLM call",
      nodes: ["r2", "r3", "catalogue"],
      edges: ["r2-r3", "cat-r3"],
      artifact: {
        label: "Expected output shape",
        kind: "code",
        body: '{\n  "selected_tool": "read_file",\n  "parameters": { "path": "pager.py" }\n}',
      },
    },
    {
      title: "Execute the tool",
      actor: "Plain code",
      nodes: ["r3", "exec"],
      edges: ["r3-ex"],
    },
    {
      title: "Synthesis: write the fix",
      actor: "LLM call",
      nodes: ["exec", "synth"],
      edges: ["ex-syn"],
    },
    {
      title: "The tests decide",
      actor: "Sandbox",
      nodes: ["synth", "tests"],
      edges: ["syn-t"],
    },
  ],
  run: "python -m patterns.s02_incremental_tool_agent.agent pager_bugs",
  files: [
    { path: "patterns/s02_incremental_tool_agent/tools.py", what: "read_file, search_code, run_tests, list_files" },
    { path: "patterns/s02_incremental_tool_agent/agent.py", what: "the three rounds, execution, synthesis" },
  ],
};

/* ───────────────────────────── S3 ───────────────────────────── */

const s3: RawPattern = {
  id: "self-reflection",
  code: "S3",
  group: "Single agent",
  title: "Self-Reflection",
  scenario: "Implement a spec-heavy function",
  task: "parse_duration, roman_to_int",
  llmCalls: "3 minimum, then 2 per revision (diagnose, revise)",
  verifiedBy: "Hidden unit tests, re-run after every revision",
  diagram: {
    height: 360,
    nodes: [
      { id: "spec", label: "Spec", sub: "many rules", kind: "input", x: 20, y: 40, w: 120, h: 72 },
      { id: "plan", label: "Planner", sub: "draft plan", kind: "llm", x: 175, y: 40, w: 130, h: 72 },
      { id: "crit", label: "Reflector", sub: "critique the plan", kind: "llm", x: 340, y: 40, w: 140, h: 72 },
      { id: "exec", label: "Executor", sub: "write the code", kind: "llm", x: 515, y: 40, w: 140, h: 72 },
      { id: "sb", label: "Sandbox", sub: "run tests", kind: "tool", x: 690, y: 40, w: 130, h: 72 },
      { id: "done", label: "Solved", sub: "all pass", kind: "data", x: 855, y: 40, w: 85, h: 72 },
      { id: "diag", label: "Reflector", sub: "diagnose the failures in words", kind: "llm", x: 515, y: 235, w: 305, h: 64 },
    ],
    edges: [
      { id: "s-p", from: "spec", to: "plan" },
      { id: "p-c", from: "plan", to: "crit", label: "draft" },
      { id: "c-e", from: "crit", to: "exec", label: "plan" },
      { id: "e-sb", from: "exec", to: "sb" },
      { id: "sb-d", from: "sb", to: "done", label: "pass" },
      { id: "sb-diag", from: "sb", to: "diag", fs: "b", ts: "t", fOff: 0, tOff: 88, label: "fail" },
      { id: "diag-e", from: "diag", to: "exec", fs: "t", ts: "b", fOff: -82, tOff: 0, label: "revise" },
    ],
    notes: [
      { x: 20, y: 170, text: "Reflection 1: before any code is written", anchor: "start" },
      { x: 20, y: 188, text: "Reflection 2: after a failing test run", anchor: "start" },
      { x: 20, y: 280, text: "Loop is capped at max_revisions (default 3).", anchor: "start" },
    ],
  },
  steps: [
    {
      title: "The specification",
      actor: "Input",
      nodes: ["spec"],
    },
    {
      title: "Plan",
      actor: "LLM call",
      nodes: ["spec", "plan"],
      edges: ["s-p"],
    },
    {
      title: "Reflect on the plan",
      actor: "LLM call",
      nodes: ["plan", "crit"],
      edges: ["p-c"],
    },
    {
      title: "Implement",
      actor: "LLM call",
      nodes: ["crit", "exec"],
      edges: ["c-e"],
    },
    {
      title: "Run the tests",
      actor: "Sandbox",
      nodes: ["exec", "sb", "done"],
      edges: ["e-sb", "sb-d"],
    },
    {
      title: "Diagnose the failures",
      actor: "LLM call",
      nodes: ["sb", "diag"],
      edges: ["sb-diag"],
    },
    {
      title: "Revise and re-test",
      actor: "LLM call",
      nodes: ["diag", "exec", "sb"],
      edges: ["diag-e", "e-sb"],
    },
  ],
  run: "python -m patterns.s03_self_reflection.agent parse_duration",
  files: [
    { path: "patterns/s03_self_reflection/planner.py", what: "draft plan" },
    { path: "patterns/s03_self_reflection/reflector.py", what: "plan critique and failure diagnosis" },
    { path: "patterns/s03_self_reflection/executor.py", what: "implement and revise" },
  ],
};

/* ───────────────────────────── M1 ───────────────────────────── */

const m1: RawPattern = {
  id: "debate",
  code: "M1",
  group: "Multi-agent",
  title: "Debate",
  scenario: "Code review of a pull request",
  task: "review_orders",
  llmCalls: "3 × rounds + 1 (7 with the default 2 rounds)",
  verifiedBy: "Judge’s patched file run against hidden tests",
  diagram: {
    height: 400,
    groups: [{ x: 185, y: 12, w: 360, h: 376, label: "Debate rounds: each reviewer answers the other two" }],
    nodes: [
      { id: "pr", label: "Pull request", sub: "diff + spec", kind: "input", x: 20, y: 160, w: 130, h: 70 },
      { id: "base", label: "Baseline run", sub: "tests on the PR\nas submitted", kind: "tool", x: 20, y: 300, w: 130, h: 64 },
      { id: "sec", label: "Security Engineer", sub: "injection, data exposure", kind: "llm", x: 215, y: 50, w: 215, h: 72 },
      { id: "cor", label: "Correctness Reviewer", sub: "edge cases, docstrings", kind: "llm", x: 215, y: 164, w: 215, h: 72 },
      { id: "mnt", label: "Pragmatic Maintainer", sub: "callers, compatibility", kind: "llm", x: 215, y: 278, w: 215, h: 72 },
      { id: "judge", label: "Judge", sub: "verdict +\npatched file", kind: "llm", x: 625, y: 160, w: 130, h: 78 },
      { id: "sb", label: "Sandbox", sub: "hidden tests on\nthe patched file", kind: "tool", x: 805, y: 160, w: 135, h: 78 },
    ],
    edges: [
      { id: "pr-base", from: "pr", to: "base" },
      { id: "pr-sec", from: "pr", to: "sec", fs: "r", ts: "l", mid: 168 },
      { id: "pr-cor", from: "pr", to: "cor", fs: "r", ts: "l", mid: 168 },
      { id: "pr-mnt", from: "pr", to: "mnt", fs: "r", ts: "l", mid: 168 },
      { id: "m-sc", from: "sec", to: "cor", fs: "b", ts: "t", both: true, label: "rebut" },
      { id: "m-cm", from: "cor", to: "mnt", fs: "b", ts: "t", both: true, label: "rebut" },
      { id: "deb-j", from: "cor", to: "judge", fs: "r", ts: "l", pts: [[545, 200], [625, 200]], label: "transcript" },
      { id: "j-sb", from: "judge", to: "sb", label: "patch" },
    ],
  },
  steps: [
    {
      title: "The pull request",
      actor: "Plain code",
      nodes: ["pr", "base"],
      edges: ["pr-base"],
      artifact: {
        label: "Excerpt of the code under review (task_data/review_orders)",
        kind: "code",
        body: 'def get_orders(conn, user_id, status=None):\n    query = "SELECT ... WHERE user_id = " + str(user_id)\n    if status:\n        query += " AND status = \'" + status + "\'"\n    ...\n\ndef latest_order(conn, user_id):\n    orders = get_orders(conn, user_id)\n    return orders[-1]',
      },
    },
    {
      title: "Opening statements",
      actor: "Several LLM calls",
      nodes: ["pr", "sec", "cor", "mnt"],
      edges: ["pr-sec", "pr-cor", "pr-mnt"],
    },
    {
      title: "Rebuttal rounds",
      actor: "Several LLM calls",
      nodes: ["sec", "cor", "mnt"],
      edges: ["m-sc", "m-cm"],
    },
    {
      title: "The judge decides",
      actor: "LLM call",
      nodes: ["cor", "judge"],
      edges: ["deb-j"],
    },
    {
      title: "The tests decide",
      actor: "Sandbox",
      nodes: ["judge", "sb"],
      edges: ["j-sb"],
    },
  ],
  run: "python -m patterns.m01_debate.agent review_orders",
  files: [{ path: "patterns/m01_debate/agent.py", what: "debaters, rounds, judge" }],
};

/* ───────────────────────────── M2 ───────────────────────────── */

const m2: RawPattern = {
  id: "voting",
  code: "M2",
  group: "Multi-agent",
  title: "Voting",
  scenario: "Pick the best of N generated solutions",
  task: "merge_intervals, roman_to_int, parse_duration",
  llmCalls: "N, run in parallel (3 to 7)",
  verifiedBy: "Winner checked against hidden tests (not used to vote)",
  diagram: {
    height: 360,
    nodes: [
      { id: "spec", label: "Spec", sub: "no tests needed", kind: "input", x: 20, y: 130, w: 120, h: 72 },
      { id: "c1", label: "Candidate 1", sub: "straightforward", kind: "llm", x: 180, y: 25, w: 170, h: 52 },
      { id: "c2", label: "Candidate 2", sub: "defensive", kind: "llm", x: 180, y: 100, w: 170, h: 52 },
      { id: "c3", label: "Candidate 3", sub: "pythonic", kind: "llm", x: 180, y: 175, w: 170, h: 52 },
      { id: "cn", label: "Candidate N", sub: "other style hints", kind: "llm", x: 180, y: 250, w: 170, h: 52 },
      { id: "probe", label: "Run on probe\ninputs", sub: "same inputs for all", kind: "tool", x: 400, y: 125, w: 140, h: 82 },
      { id: "group", label: "Group by\nidentical output", sub: "behaviour signatures", kind: "tool", x: 590, y: 125, w: 140, h: 82 },
      { id: "win", label: "Winner", sub: "largest group", kind: "data", x: 780, y: 125, w: 160, h: 82 },
      { id: "hidden", label: "Hidden tests", sub: "score every candidate", kind: "tool", x: 780, y: 270, w: 160, h: 56 },
    ],
    edges: [
      { id: "s-c1", from: "spec", to: "c1" },
      { id: "s-c2", from: "spec", to: "c2" },
      { id: "s-c3", from: "spec", to: "c3" },
      { id: "s-cn", from: "spec", to: "cn" },
      { id: "c1-p", from: "c1", to: "probe" },
      { id: "c2-p", from: "c2", to: "probe" },
      { id: "c3-p", from: "c3", to: "probe" },
      { id: "cn-p", from: "cn", to: "probe" },
      { id: "p-g", from: "probe", to: "group", label: "outputs" },
      { id: "g-w", from: "group", to: "win", label: "largest" },
      { id: "w-h", from: "win", to: "hidden", dashed: true, label: "audit only" },
    ],
  },
  steps: [
    {
      title: "Start from a spec",
      actor: "Input",
      nodes: ["spec"],
    },
    {
      title: "Generate N candidates",
      actor: "Several LLM calls",
      nodes: ["spec", "c1", "c2", "c3", "cn"],
      edges: ["s-c1", "s-c2", "s-c3", "s-cn"],
    },
    {
      title: "Run all of them on the same probes",
      actor: "Plain code",
      nodes: ["c1", "c2", "c3", "cn", "probe"],
      edges: ["c1-p", "c2-p", "c3-p", "cn-p"],
    },
    {
      title: "Group and vote",
      actor: "Plain code",
      nodes: ["probe", "group", "win"],
      edges: ["p-g", "g-w"],
      matrix: {
        caption: "Illustrative values, not a recorded run. Cells are the output for each probe; colour marks the behaviour group.",
        head: ["Probe", "C1", "C2", "C3", "C4", "C5"],
        rows: [
          ["[(1,3),(2,6)]", "[(1,6)]", "[(1,6)]", "[(1,6)]", "[(1,6)]", "[(1,6)]"],
          ["[(1,2),(2,3)]", "[(1,3)]", "[(1,3)]", "[(1,3)]", "[(1,2),(2,3)]", "[(1,3)]"],
          ["[(3,1)]", "ValueError", "ValueError", "ValueError", "[(3,1)]", "ValueError"],
        ],
        group: [0, 0, 0, 1, 0],
      },
    },
    {
      title: "Audit against hidden tests",
      actor: "Sandbox",
      nodes: ["win", "hidden"],
      edges: ["w-h"],
    },
    {
      title: "Where voting fails",
      actor: "Input",
      nodes: ["group", "win"],
      matrix: {
        caption: "Illustrative values, not a recorded run. Four of five share a blind spot; the one correct candidate loses the vote.",
        head: ["Probe", "C1", "C2", "C3", "C4", "C5"],
        rows: [
          ["roman_to_int(\"MCMXCIV\")", "1994", "1994", "1994", "1994", "1994"],
          ["roman_to_int(\"IIII\")", "4", "4", "4", "4", "ValueError"],
          ["roman_to_int(\"VX\")", "5", "5", "5", "5", "ValueError"],
        ],
        group: [0, 0, 0, 0, 1],
      },
    },
  ],
  run: "python -m patterns.m02_voting.agent merge_intervals",
  files: [{ path: "patterns/m02_voting/agent.py", what: "candidates, probe runner, grouping, audit" }],
};

/* ───────────────────────────── M3 ───────────────────────────── */

const m3: RawPattern = {
  id: "subagent-spawning",
  code: "M3",
  group: "Multi-agent",
  title: "Sub-agent Spawning",
  scenario: "Modernise a four-module legacy codebase",
  task: "legacy_shop",
  llmCalls: "1 spawner + one per sub-agent (2 to 4) + 1 PR description",
  verifiedBy: "Existing test suite plus static modernisation metrics",
  diagram: {
    height: 420,
    groups: [{ x: 355, y: 12, w: 245, h: 396, label: "Parallel, isolated context" }],
    nodes: [
      { id: "task", label: "Task +\ncodebase", sub: "4 modules", kind: "input", x: 20, y: 177, w: 120, h: 86 },
      { id: "spawner", label: "Spawner", sub: "decides who and\nhow many", kind: "llm", x: 185, y: 177, w: 135, h: 86 },
      { id: "a", label: "Sub-agent A", sub: "owns inventory.py", kind: "llm", runtime: true, x: 375, y: 60, w: 205, h: 56 },
      { id: "b", label: "Sub-agent B", sub: "owns pricing.py", kind: "llm", runtime: true, x: 375, y: 148, w: 205, h: 56 },
      { id: "c", label: "Sub-agent C", sub: "owns orders.py", kind: "llm", runtime: true, x: 375, y: 236, w: 205, h: 56 },
      { id: "d", label: "Sub-agent D", sub: "owns reports.py", kind: "llm", runtime: true, x: 375, y: 324, w: 205, h: 56 },
      { id: "integ", label: "Integrator", sub: "merge the files", kind: "tool", x: 640, y: 177, w: 120, h: 86 },
      { id: "tests", label: "Existing tests", sub: "behaviour kept?", kind: "tool", x: 810, y: 80, w: 130, h: 56 },
      { id: "metrics", label: "Static metrics", sub: "types, docstrings,\nprint() calls", kind: "tool", x: 810, y: 187, w: 130, h: 66 },
      { id: "pr", label: "PR description", sub: "written by LLM", kind: "llm", x: 810, y: 295, w: 130, h: 56 },
    ],
    edges: [
      { id: "t-s", from: "task", to: "spawner" },
      { id: "s-a", from: "spawner", to: "a", mid: 340 },
      { id: "s-b", from: "spawner", to: "b", mid: 340 },
      { id: "s-c", from: "spawner", to: "c", mid: 340 },
      { id: "s-d", from: "spawner", to: "d", mid: 340 },
      { id: "a-i", from: "a", to: "integ", mid: 620 },
      { id: "b-i", from: "b", to: "integ", mid: 620 },
      { id: "c-i", from: "c", to: "integ", mid: 620 },
      { id: "d-i", from: "d", to: "integ", mid: 620 },
      { id: "i-t", from: "integ", to: "tests" },
      { id: "i-m", from: "integ", to: "metrics" },
      { id: "i-p", from: "integ", to: "pr" },
    ],
  },
  steps: [
    {
      title: "Task and codebase",
      actor: "Plain code",
      nodes: ["task"],
    },
    {
      title: "The Spawner designs the team",
      actor: "LLM call",
      nodes: ["task", "spawner"],
      edges: ["t-s"],
      artifact: {
        label: "Shape of the Spawner’s output (from the prompt)",
        kind: "code",
        body: '{\n  "strategy": "one sentence",\n  "subagents": [\n    { "name": "Logging Migration Specialist (inventory.py)",\n      "file": "inventory.py",\n      "persona": "2 sentences...",\n      "instructions": "what is special about this file" }\n  ]\n}',
      },
    },
    {
      title: "Sub-agents work in parallel",
      actor: "Several LLM calls",
      nodes: ["spawner", "a", "b", "c", "d"],
      edges: ["s-a", "s-b", "s-c", "s-d"],
    },
    {
      title: "Integrate and verify",
      actor: "Plain code",
      nodes: ["a", "b", "c", "d", "integ", "tests", "metrics"],
      edges: ["a-i", "b-i", "c-i", "d-i", "i-t", "i-m"],
    },
    {
      title: "Write the PR description",
      actor: "LLM call",
      nodes: ["integ", "pr"],
      edges: ["i-p"],
    },
  ],
  run: "python -m patterns.m03_subagent_spawning.agent legacy_shop",
  files: [
    { path: "patterns/m03_subagent_spawning/spawner.py", what: "designs the team" },
    { path: "patterns/m03_subagent_spawning/subagent.py", what: "isolated per-file worker" },
    { path: "patterns/m03_subagent_spawning/metrics.py", what: "static modernisation score" },
  ],
};

/* ───────────────────────────── M4 ───────────────────────────── */

const m4: RawPattern = {
  id: "swarm",
  code: "M4",
  group: "Multi-agent",
  title: "Swarm",
  scenario: "Build a class until the suite is green",
  task: "lru_cache, parse_duration",
  llmCalls: "Varies, up to max_hops (the Tester uses none)",
  verifiedBy: "The Tester runs the real test suite at every hop",
  diagram: {
    height: 390,
    groups: [{ x: 10, y: 322, w: 940, h: 58, label: "Blackboard: current code · latest test report · feedback" }],
    nodes: [
      { id: "disp", label: "Dispatcher", sub: "starts the run", kind: "input", x: 20, y: 160, w: 110, h: 72 },
      { id: "coder", label: "Coder", sub: "write or rewrite", kind: "llm", x: 180, y: 160, w: 130, h: 72 },
      { id: "tester", label: "Tester", sub: "runs tests, routes\nby rules (no LLM)", kind: "tool", x: 390, y: 160, w: 150, h: 72 },
      { id: "dbg", label: "Debugger", sub: "patch from failures", kind: "llm", x: 390, y: 25, w: 150, h: 60 },
      { id: "rev", label: "Reviewer", sub: "spec compliance", kind: "llm", x: 640, y: 160, w: 140, h: 72 },
      { id: "done", label: "Done", sub: "", kind: "data", x: 840, y: 160, w: 100, h: 72 },
    ],
    edges: [
      { id: "d-c", from: "disp", to: "coder" },
      { id: "c-t", from: "coder", to: "tester", label: "handoff" },
      { id: "t-d", from: "tester", to: "dbg", fs: "t", ts: "b", fOff: -30, tOff: -30, label: "small failure", labelLeft: true },
      { id: "d-t", from: "dbg", to: "tester", fs: "b", ts: "t", fOff: 30, tOff: 30, label: "patched" },
      { id: "t-c", from: "tester", to: "coder", fs: "b", ts: "b", pts: [[465, 232], [465, 275], [245, 275], [245, 232]], label: "fails badly or stalls: rewrite" },
      { id: "t-r", from: "tester", to: "rev", label: "all green" },
      { id: "r-done", from: "rev", to: "done", label: "approve" },
      { id: "r-d", from: "rev", to: "dbg", pts: [[710, 160], [710, 55], [540, 55]], label: "changes needed" },
      { id: "veto", from: "tester", to: "done", dashed: true, pts: [[510, 232], [510, 300], [890, 300], [890, 232]], label: "veto: edit broke green suite, revert and finish" },
    ],
  },
  steps: [
    {
      title: "The Dispatcher starts the run",
      actor: "Plain code",
      nodes: ["disp"],
    },
    {
      title: "Coder writes the implementation",
      actor: "LLM call",
      nodes: ["disp", "coder"],
      edges: ["d-c"],
    },
    {
      title: "Tester runs the real tests and routes",
      actor: "Sandbox",
      nodes: ["coder", "tester"],
      edges: ["c-t"],
    },
    {
      title: "Debugger patches, Tester re-checks",
      actor: "LLM call",
      nodes: ["tester", "dbg"],
      edges: ["t-d", "d-t"],
    },
    {
      title: "Rewrite when patching is not working",
      actor: "Plain code",
      nodes: ["tester", "coder"],
      edges: ["t-c"],
    },
    {
      title: "Reviewer checks the spec once green",
      actor: "LLM call",
      nodes: ["tester", "rev", "dbg", "done"],
      edges: ["t-r", "r-done", "r-d", "veto"],
    },
    {
      title: "The path emerges",
      actor: "Input",
      nodes: ["disp", "coder", "tester", "dbg", "rev", "done"],
      path: [
        { label: "Clean first draft", steps: ["dispatcher", "coder", "tester", "reviewer", "done"] },
        { label: "Needs debugging", steps: ["dispatcher", "coder", "tester", "debugger", "tester", "debugger", "tester", "reviewer", "done"] },
        { label: "Rewrite needed", steps: ["dispatcher", "coder", "tester", "coder", "tester", "reviewer", "done"], note: "Illustrative paths; the demo prints the real one after each run." },
      ],
    },
  ],
  run: "python -m patterns.m04_swarm.agent lru_cache",
  files: [{ path: "patterns/m04_swarm/agent.py", what: "blackboard, agents, routing rules" }],
};

const raw: RawPattern[] = [s1, s2, s3, m1, m2, m3, m4];

export const PATTERNS: Pattern[] = raw.map((p) => {
  const c = COPY[p.code];
  return {
    ...p,
    summary: c.summary,
    context: c.context,
    problem: c.problem,
    solution: c.solution,
    useWhen: c.useWhen,
    tradeoff: c.tradeoff,
    consequences: [
      ...c.pros.map(([attribute, text]) => ({ attribute, effect: "pro" as const, text })),
      ...c.cons.map(([attribute, text]) => ({ attribute, effect: "con" as const, text })),
    ],
    steps: p.steps.map((st, i) => ({ ...st, ...c.steps[i] })),
  };
});

export const foundations = {
  legend: [
    { kind: "input", name: "Input", text: "The task or a human-supplied artifact." },
    { kind: "llm", name: "LLM call", text: "A language-model call. Output can vary between runs." },
    { kind: "tool", name: "Plain code", text: "Deterministic code: file reads, test runs, routing rules." },
    { kind: "data", name: "Artifact", text: "Something produced and passed on, such as a prompt, plan or patch." },
  ] as { kind: Kind; name: string; text: string }[],
};
