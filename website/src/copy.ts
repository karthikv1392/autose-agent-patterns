// Prose for each pattern, in the order: context, problem, solution, use when, trade-off,
// then quality-attribute pros and cons. Kept separate from the diagrams in data.ts.

type Q = [attribute: string, text: string];

export type PatternCopy = {
  summary: string;
  context: string;
  problem: string;
  solution: string;
  useWhen: string[];
  tradeoff: string;
  pros: Q[];
  cons: Q[];
  steps: { body: string; points?: string[] }[];
};

export const COPY: Record<string, PatternCopy> = {
  S1: {
    summary: "Gather repository, test and environment context before the LLM call.",
    context: "Bug reports are short and vague, but the repository, the test suite and the runtime are all available to the agent.",
    problem: "Accuracy depends on the context in the prompt. A model that sees only the report has to guess which file and which behaviour is wrong, while gathering more context adds latency and prompt length.",
    solution: "Run plain code that reads the environment, maps the repository, runs the tests and reads the source. Put the results in the prompt with the user's request and call the LLM once.",
    useWhen: ["Reports are vague or underspecified", "Tests and files can be read automatically", "The repository fits in a prompt"],
    tradeoff: "Edits are grounded in failing tests and real code, at the cost of extra setup time and a longer prompt.",
    pros: [
      ["Accuracy", "The model sees the failing assertions and the code behind them."],
      ["Observability", "The enriched prompt shows exactly what the agent knew."],
      ["Modifiability", "A new context source is one more gatherer function."],
    ],
    cons: [
      ["Latency", "Tests and file reads run before the first LLM call."],
      ["Accuracy", "Truncated or irrelevant context can mislead the model."],
      ["Security", "Gathering context executes code, and the sandbox is process-level isolation only."],
    ],
    steps: [
      { body: "The report names a symptom. It does not name a function, an input or an expected value." },
      { body: "The demo first sends the request to the model as typed, as a control. The model has not seen the repository, so it writes code for files it cannot read.",
        points: ["The prompt is the sentence above plus “The project is a small Python package.”", "The patch is scored by the same hidden tests."] },
      { body: "Four plain functions run before any LLM call: they read the environment, map the repository, run the tests and read the source. Whatever fails in the test run describes the bug." },
      { body: "The four results go into one prompt under labelled headings, followed by an instruction to treat docstrings as the specification. Long test output is truncated." },
      { body: "The model returns the complete updated files, which are parsed and written over the originals." },
      { body: "The patched files run against the hidden tests in a separate process. The pass count is the result." },
    ],
  },
  S2: {
    summary: "Split tool selection into analyse, choose and parameter rounds.",
    context: "A coding agent has tools such as read_file, search_code and run_tests. It must pick one and fill in its arguments before it can fix a bug.",
    problem: "Observability and reliability suffer when tool choice and argument formatting happen in one call, because a wrong call cannot be traced to its cause. Splitting the decision costs extra calls and tokens.",
    solution: "Query the LLM in rounds. Round 1 analyses the report, round 2 plans and picks a tool, round 3 returns the exact call as JSON. Each round sees the goal and all earlier rounds. Run the tool, then make a final call to write the fix.",
    useWhen: ["Tool calls need a reviewable reason", "Small models mix up reasoning and formatting", "You are teaching how agents choose tools"],
    tradeoff: "Every decision can be inspected, but there are four sequential calls and later prompts repeat earlier rounds.",
    pros: [
      ["Observability", "Each round is recorded, so a failure points to analysis, tool choice, parameters or fix."],
      ["Accuracy", "A written hypothesis comes before the action."],
      ["Reliability", "Key aliases are accepted and bad calls become visible error text."],
    ],
    cons: [
      ["Cost", "Four LLM calls, and each round repeats the earlier ones."],
      ["Latency", "Rounds run in sequence."],
      ["Adaptability", "One tool call only; the agent cannot look at the result and choose again."],
    ],
    steps: [
      { body: "The agent has the report and the file names. It has read no code yet." },
      { body: "The model is asked what is probably wrong and what it needs to see. It is told not to propose a fix." },
      { body: "The model gets the goal, its analysis and a description of each tool. It writes a short plan and picks one tool, with a reason, but gives no parameters yet." },
      { body: "A separate call turns the choice into JSON. Small models often change the key names, so tool_name and tool_input are accepted as aliases." },
      { body: "The named function is called. An unknown tool or bad arguments produce error text that goes on to the next step." },
      { body: "The final call gets the goal, both earlier rounds, the tool call and its output, and returns the complete changed files. If the output did not show the code, the model says so and still tries." },
      { body: "The patch runs against the hidden tests. A failure can be traced to the round that caused it." },
    ],
  },
  S3: {
    summary: "Critique the plan before coding and diagnose test failures before revising.",
    context: "A task has a precise specification with many small rules, and a test suite can run the result.",
    problem: "Accuracy needs checking at more than one point, since a single generation rarely covers every rule. Each check adds calls, and the model's own critique can be wrong.",
    solution: "Draft a plan and have a reflector critique it against the spec before any code is written. Implement and run the tests. When they fail, have the reflector explain the cause from the test output, revise the code and test again, up to a fixed number of revisions.",
    useWhen: ["The spec has many small rules", "Tests can run the result", "A first attempt is usually close but incomplete"],
    tradeoff: "Failures are fixed with a stated cause, at the price of at least three calls and two more per revision.",
    pros: [
      ["Accuracy", "The second reflection uses real test output."],
      ["Observability", "Written diagnoses explain each revision."],
      ["Predictability", "Revisions are capped."],
    ],
    cons: [
      ["Reliability", "The plan critique is unverified, and a diagnosis can name the wrong cause."],
      ["Cost", "Three or more calls, two per revision."],
      ["Latency", "Plan, critique, code and test run in sequence."],
    ],
    steps: [
      { body: "For parse_duration the spec has units in descending order, each at most once, bare integers as seconds, and several kinds of input that must raise ValueError." },
      { body: "The planner turns the spec into numbered steps, including edge cases." },
      { body: "The reflector checks the plan against the spec, lists issues and rewrites the steps if needed. No code exists yet, so a missing rule costs one sentence to fix.",
        points: ["This critique is the model's opinion; nothing has run yet."] },
      { body: "The executor writes the complete file from the final plan." },
      { body: "The code runs against the hidden tests. If everything passes, the run ends." },
      { body: "The reflector gets the spec, the code, the test output and earlier diagnoses, and explains the cause in words. Earlier diagnoses are included so it does not repeat one that failed." },
      { body: "The executor revises the code using the diagnosis and the tests run again. This repeats until the suite passes or the revision limit is reached." },
    ],
  },
  M1: {
    summary: "Reviewers with different priorities rebut each other; a judge writes the patch.",
    context: "A pull request touches several concerns at once, such as security, correctness and compatibility, and a wrong merge is expensive.",
    problem: "Review reliability improves when reviewers challenge each other, but each reviewer and round adds latency and cost, and models tend to agree.",
    solution: "Give the same code to a security reviewer, a correctness reviewer and a maintainer. Each states issues, then answers the others over one or more rounds. A judge reads the transcript and writes the verdict and a patched file, and the patch is tested.",
    useWhen: ["A change touches several concerns", "A wrong merge is costly", "One reviewer keeps missing things"],
    tradeoff: "Conflicts between fixes surface before merge, at the cost of 3 × rounds + 1 calls.",
    pros: [
      ["Accuracy", "Rebuttals expose fixes that would break callers."],
      ["Auditability", "The transcript records why the patch looks the way it does."],
      ["Security", "A security reviewer always reads the code."],
    ],
    cons: [
      ["Cost", "3 × rounds + 1 calls."],
      ["Latency", "Rounds run in sequence before the judge starts."],
      ["Reliability", "A persuasive judge can still write a wrong patch."],
    ],
    steps: [
      { body: "The harness shows the code under review and runs the hidden tests on it as submitted." },
      { body: "Three agents with different personas review the same numbered code. Each lists at most four issues with severity, line, reason and fix, and ends with APPROVE or REQUEST_CHANGES.",
        points: ["Within a round, reviewers do not see each other."] },
      { body: "Each reviewer now gets the transcript. The prompt requires naming another reviewer and accepting or rejecting their point, and flagging any fix that would break existing callers.",
        points: ["The demo allows 1 to 3 rounds."] },
      { body: "The judge answers in fixed sections: verdict on the PR as submitted, agreed issues, open disagreements, rationale and the full patched file. It is told to check the patch against every docstring." },
      { body: "The patched file replaces the original and the hidden tests run. A persuasive but wrong verdict still fails." },
    ],
  },
  M2: {
    summary: "Generate N candidates and choose the behaviour most of them share.",
    context: "A function has to be written from a specification. Candidates are cheap to generate and can be run on chosen inputs, but there is no trusted test suite yet.",
    problem: "Accuracy of a single sample varies, and asking an LLM which solution looks best is a weak check. More samples cost more and only help when their errors are independent.",
    solution: "Generate N candidates in parallel with different style hints. Run all of them on the same probe inputs, group candidates that print identical output, and pick the largest group. Hidden tests check the winner afterwards.",
    useWhen: ["A spec exists but tests do not", "Output is deterministic and easy to compare", "Single samples vary a lot"],
    tradeoff: "Selection needs no tests or LLM judge, but candidates that share a mistake outvote the correct one.",
    pros: [
      ["Accuracy", "Independent random errors are outvoted."],
      ["Predictability", "Selection is execution and counting, with no LLM."],
      ["Latency", "Candidates run in parallel."],
    ],
    cons: [
      ["Accuracy", "Shared mistakes win the vote."],
      ["Cost", "N times the tokens of one attempt."],
      ["Modifiability", "Probe inputs define what counts as the same behaviour; weak probes group different programs."],
    ],
    steps: [
      { body: "Only a specification and a list of probe inputs are needed. The hidden tests are held back until the vote is over." },
      { body: "N agents answer the same prompt in parallel at temperature 0.9. Each gets a different style hint, such as defensive or rule-by-rule." },
      { body: "Every candidate runs on the same inputs. The output for all probes forms its behaviour signature. A crash is also a signature." },
      { body: "Candidates with identical signatures form a group. The largest group wins; ties go to the lower candidate number." },
      { body: "Now the tests run on every candidate. They show whether the vote was right and how far the winner is from the best candidate. They are not used to choose." },
      { body: "Voting helps only when mistakes are independent. If most candidates share a blind spot they agree on the wrong behaviour. On roman_to_int, models often accept non-canonical numerals such as IIII.",
        points: ["The demo reports the average candidate and the best of N next to the vote."] },
    ],
  },
  M3: {
    summary: "A spawner designs one specialist per module; they refactor in parallel.",
    context: "A refactor or migration splits by module, an existing test suite can check behaviour, and the workers needed depend on the code.",
    problem: "Performance and accuracy suffer when one agent handles a whole repository, while parallel workers risk interface drift because they cannot see each other's changes.",
    solution: "A spawner reads a summary of the repository and returns the sub-agents to create: a name, an owned file, a persona and notes for each. Each sub-agent sees its own file and the signatures of the others, and they run in parallel. An integrator merges the files and runs the existing tests and static checks.",
    useWhen: ["The change decomposes by file or module", "A regression suite exists", "The right team depends on the repository"],
    tradeoff: "Work runs in parallel with small contexts, but conflicts between modules appear only when the files are merged.",
    pros: [
      ["Performance", "Wall time is the slowest worker, not the sum."],
      ["Adaptability", "The team is designed per repository."],
      ["Accuracy", "Each worker has a small, focused context."],
    ],
    cons: [
      ["Reliability", "Cross-module problems appear only at integration."],
      ["Accuracy", "A poor split by the spawner limits every worker."],
      ["Cost", "One call per worker, plus the spawner and the PR description."],
    ],
    steps: [
      { body: "The task is to add type hints and docstrings and replace print() with logging, keeping behaviour. The harness records the existing test result and a modernisation score first." },
      { body: "The spawner sees each file's size, definitions and print count, and returns JSON with a strategy and a list of sub-agents. Each has a name, one owned file, a persona and notes.",
        points: ["A file the spawner forgets still gets a default worker."] },
      { body: "Each sub-agent sees its own file and the public signatures of the other modules, read-only. It is told to keep every public name, signature and behaviour.",
        points: ["A reply that is not valid Python is rejected and the original file is kept."] },
      { body: "The integrator collects the new files. The existing test suite runs on the merged code and the static metrics are recomputed." },
      { body: "A last call writes a pull request description from the before and after scores, the changed files and the test result. The demo also reports parallel wall time against the sum of the worker times." },
    ],
  },
  M4: {
    summary: "Agents hand work to each other until the tests pass; no manager.",
    context: "Getting code to pass its tests is a loop of unknown length, and a test run says what is wrong at each pass.",
    problem: "Adaptability needs a route that follows the run, but without a central manager the loop can circle and the path is hard to predict.",
    solution: "Agents share a blackboard with the current code and the latest test report. A coder writes, a tester runs the tests and routes by fixed rules, a debugger patches, and a reviewer checks the spec once tests pass. Each agent names the next one. A hop limit, a review cap and a revert-to-last-green rule bound the run.",
    useWhen: ["The task is an iterate-until-green loop", "The number of rounds is unknown", "A cheap check can steer routing"],
    tradeoff: "The route fits each run, but paths differ between runs and cost varies.",
    pros: [
      ["Adaptability", "A clean draft goes straight to review; a broken one loops."],
      ["Predictability", "The tester routes by rules, not LLM judgement."],
      ["Reliability", "The hop limit, review cap and revert rule bound the run."],
    ],
    cons: [
      ["Predictability", "Different runs take different paths."],
      ["Auditability", "The path is known only after the run."],
      ["Cost", "The number of calls varies, up to the hop limit."],
    ],
    steps: [
      { body: "The task goes to the coder. After that each agent names the next. The blackboard is the only shared state." },
      { body: "The coder writes the complete file and ends its reply with a hand-off such as HANDOFF: tester. Hand-offs are parsed from the text and limited to allowed targets." },
      { body: "The tester is code, not an LLM. It runs the suite and routes by fixed rules.",
        points: ["All tests pass: reviewer.", "Some fail but progress is being made: debugger.", "Fewer than half pass, or two fixes made no progress: coder, for a rewrite."] },
      { body: "The debugger gets the spec, the code and the failing output, and patches the code. The tester runs again, so this pair can repeat." },
      { body: "If the draft is badly wrong or patches stall, the tester sends the work back to the coder with the feedback and an instruction to simplify." },
      { body: "The reviewer answers APPROVE or CHANGES. Changes go to the debugger and back through the tester.",
        points: ["If a requested edit breaks a green suite, the tester reverts to the last green version and finishes.", "Review requests are capped at two."] },
      { body: "Runs on the same task can take different routes. At the hop limit the swarm returns the best version seen, not the latest." },
    ],
  },
  M5: {
    summary: "Search earlier solutions, adapt what fits, and save validated ones for next time.",
    context: "Software teams keep meeting the same kinds of problem, such as input validation, retries with backoff or strict parsers. A stateless agent solves each one from scratch in every session, which wastes time and tokens.",
    problem: "Performance, consistency and cost improve when a good solution is reused, but a stale or wrong skill creates reliability, security and maintenance obligations.",
    solution: "Keep a persistent library of skills, each with a description, tags and the task it solved. Before solving, search the summaries and load the few skills that fit. Adapt them, and save the new solution as a skill once its tests pass.",
    useWhen: ["Similar tasks recur across sessions", "Solutions can be generalised beyond one task", "A growing library of vetted code is useful"],
    tradeoff: "The library compounds useful solutions, but a stale or low-quality skill compounds errors too unless someone curates it.",
    pros: [
      ["Performance", "Known solutions cut repeated planning and the time to a working draft."],
      ["Cost", "The agent does not rediscover the same solution in every session."],
      ["Reliability", "Skills that passed tests make repeated work more consistent."],
    ],
    cons: [
      ["Maintainability", "Skills need an owner, versioning, review and retirement as dependencies change."],
      ["Reliability", "A stale skill can repeat the same mistake."],
      ["Security", "Imported or editable skills widen the trust boundary around code the agent runs."],
    ],
    steps: [
      { body: "The agent gets a task. The library already holds skills from earlier sessions: four come with the demo, and every validated run adds one." },
      { body: "The agent reads a short summary of every skill: name, tags, description and a preview of the task it solved. It does not see the code. It picks up to top_k skills that could be reused, adapted or combined, or none. A shared topic is not enough.",
        points: ["Summaries keep this prompt small however large the library grows.", "Each retrieved skill's use count goes up."] },
      { body: "Only the chosen skills are loaded in full. The agent adapts or combines them, or solves from scratch if nothing fits. It also describes the result: a name, a one-sentence description, tags, and whether it is reusable.",
        points: ["The approach is recorded as from scratch, adapted from one skill, or combined."] },
      { body: "The code runs against the hidden tests in a separate process." },
      { body: "If the tests pass and the agent marked the solution reusable, it is saved with its metadata. A failing solution is never saved, so it cannot be retrieved later and repeat its mistake." },
      { body: "The library lives on disk, so the next session starts with one more skill. In the demo, run parse_duration and then roman_to_int: both are strict parsers with fiddly rules, so the second run may find a skill worth reusing. Whether it does depends on the model, because the search is its judgement. merge_intervals is unrelated, so the search should decline." },
    ],
  },
  M6: {
    summary: "A generator drafts, a critic scores, and the draft is revised until a gate passes.",
    context: "Code often gets better when it is reviewed against explicit criteria instead of being accepted from a single generation.",
    problem: "A generator cannot reliably notice its own omissions, and a review that never leads to a revision changes nothing. An independent gate improves accuracy and reliability, but adds latency and extra calls.",
    solution: "Give writing and reviewing to separate agents. The critic scores each draft against criteria such as correctness, security and error handling, and lists what must be fixed. The generator revises against that list until the score is 7 or more with nothing left to fix, or the iteration limit is reached.",
    useWhen: ["Quality can be scored against clear criteria", "Revising is cheaper than shipping a defect", "There is a clear stopping rule"],
    tradeoff: "Drafts get stronger, but the critic only reads the code, so a pass is not proof, and without a strict budget the loop can churn.",
    pros: [
      ["Accuracy", "A separate critic checks each draft against explicit criteria."],
      ["Observability", "Scores and must-fix lists make quality failures visible."],
      ["Modifiability", "The same generator can be paired with critics for security, correctness or style."],
    ],
    cons: [
      ["Cost", "Two LLM calls per iteration."],
      ["Accuracy", "Gains level off after a few rounds, and a passing critique does not guarantee correct code."],
      ["Predictability", "A hard iteration limit is needed to stop endless revision."],
    ],
    steps: [
      { body: "The task is a specification. The loop has an iteration limit, 4 by default." },
      { body: "The generator writes a first draft from the specification alone, with a one-line rationale." },
      { body: "The critic reads the draft and scores five criteria from 1 to 10. Each gets a severity: ok, nice to have or must fix. It also gives an overall score and a must-fix list.",
        points: ["The critic never runs the code."] },
      { body: "The gate applies one rule: an overall score of at least 7 and an empty must-fix list. On a pass the draft is accepted. On a fail the loop continues, unless the iteration limit has been reached." },
      { body: "The generator gets the task, its previous draft, the score, the feedback and the must-fix list. It must address every item without losing what was already good. The new draft goes back to the critic." },
      { body: "After every draft the demo also runs the hidden tests. The generator never sees the result. This shows where the critic and the tests disagree." },
      { body: "The loop stops at a pass or at the iteration limit. A pass means the critic is satisfied, not that the code is correct. The tests have the last word." },
    ],
  },
};
