import { useEffect, useRef, useState } from "react";
import Diagram from "./Diagram";
import SequenceDiagram from "./Sequence";
import { SEQUENCES } from "./sequences";
import { PATTERNS, foundations, type Pattern, type Step } from "./data";

function useRoute(): string {
  const read = () => window.location.hash.replace(/^#\/?/, "");
  const [route, setRoute] = useState(read);
  useEffect(() => {
    const on = () => { setRoute(read()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return route;
}

const REPO_URL = "https://github.com/karthikv1392/autose-agent-patterns";
const COURSE_URL = "https://karthikv1392.github.io/autose_course/";
const AUTHOR_URL = "https://karthikvaidhyanathan.com";

function GitHubMark() {
  return (
    <svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true" fill="currentColor">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

function Header() {
  return (
    <header className="site-header">
      <div className="wrap header-inner">
        <a className="brand" href="#/">
          <span className="brand-mark" aria-hidden="true">AS</span>
          <span>AutoSE Agent Patterns</span>
        </a>
        <a className="gh-link" href={REPO_URL} target="_blank" rel="noreferrer">
          <GitHubMark />
          <span>Code on GitHub</span>
        </a>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="site-footer">
      <div className="wrap">
        <span>
          Part of the <a href={COURSE_URL} target="_blank" rel="noreferrer">Autonomous Software Engineering</a> course.
          A companion to the Agentic Patterns field guide.
        </span>
        <span>By <a href={AUTHOR_URL} target="_blank" rel="noreferrer">Karthik Vaidhyanathan</a></span>
      </div>
    </footer>
  );
}

function Home() {
  const example = PATTERNS.find((p) => p.code === "M2")!;
  const scroll = (id: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };
  return (
    <>
      <section className="hero">
        <div className="wrap">
          <p className="eyebrow">Course material · <a href={COURSE_URL} target="_blank" rel="noreferrer">Autonomous Software Engineering</a></p>
          <h1>Agent patterns for software engineering</h1>
          <p className="lede">
            Seven ways to arrange LLM agents around a software task, such as fixing a bug, reviewing a pull request or
            refactoring a codebase. Every pattern here runs against real tests, and every page walks through how it works
            so you can see where it helps and what it costs.
          </p>
          <div className="hero-actions">
            <a className="btn primary" href="#/" onClick={scroll("what-is-a-pattern")}>What is a pattern?</a>
            <a className="btn" href={`#/${PATTERNS[0].id}`}>Jump to S1</a>
          </div>
        </div>
      </section>

      <section className="wrap section" id="what-is-a-pattern">
        <h2>What is a pattern?</h2>
        <div className="prose">
          <p>
            An architectural pattern is a proven answer to a design problem that keeps coming back. It is not code you copy.
            It records a decision, the situation that forced it, and what the decision cost.
          </p>
          <p>
            We describe each pattern the way the Software Engineering Institute’s architecture work does: as a link between a
            <strong> context</strong>, a <strong>problem</strong> and a <strong>solution</strong>.
          </p>
        </div>

        <div className="cps">
          <div>
            <h3>Context</h3>
            <p>The recurring situation where the pattern applies. Here it is always a software task an agent has to carry out.</p>
          </div>
          <div>
            <h3>Problem</h3>
            <p>The difficulty in that situation, stated as a tension between qualities such as accuracy, cost, latency and predictability. If nothing pulled the other way there would be nothing to decide.</p>
          </div>
          <div>
            <h3>Solution</h3>
            <p>The arrangement of agents, tools and checks that resolves the tension, described loosely enough to reuse on another task.</p>
          </div>
        </div>

        <p className="prose-after">
          No solution is free. A pattern buys one quality by spending another, so every page ends with pros and cons.
          Learning to read that trade-off is the main point of this site.
        </p>

        <div className="example">
          <p className="example-title">Example: {example.title} <a href={`#/${example.id}`}>read the full page</a></p>
          <dl>
            <div><dt>Context</dt><dd>{example.context}</dd></div>
            <div><dt>Problem</dt><dd>{example.problem}</dd></div>
            <div><dt>Solution</dt><dd>{example.solution}</dd></div>
          </dl>
        </div>
        <p className="source">
          Framing from Bass, Clements and Kazman, <em>Software Architecture in Practice</em> (SEI Series in Software Engineering),
          the chapter on architectural patterns.
        </p>
      </section>

      <section className="wrap section" id="patterns">
        <h2>The seven patterns</h2>
        <p className="section-intro">
          The first three change how a single agent gathers context, picks actions and checks its own work. The last four
          are about how several agents are connected.
        </p>
        <table className="index-table">
          <thead>
            <tr><th>#</th><th>Pattern</th><th>Software task</th><th className="hide-sm">In one line</th></tr>
          </thead>
          <tbody>
            {PATTERNS.map((p) => (
              <tr key={p.id} onClick={() => (window.location.hash = `/${p.id}`)}>
                <td className="code">{p.code}</td>
                <td><a href={`#/${p.id}`}>{p.title}</a><span className="group-tag">{p.group}</span></td>
                <td>{p.scenario}</td>
                <td className="hide-sm muted">{p.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="wrap section" id="how-to-read">
        <h2>Reading a pattern page</h2>
        <p className="section-intro">
          Each page gives you the context, problem and solution first. Then two diagrams. The step-through shows how a run
          unfolds: pick a step on the left or use the arrow keys, and the diagram lights up what happens in that step, keeps
          the earlier parts visible and fades the rest. The sequence diagram below it shows the same pattern as messages
          between components. The page finishes with the pros and cons.
        </p>
        <div className="legend-grid">
          {foundations.legend.map((l) => (
            <div key={l.name} className="legend-item">
              <svg viewBox="0 0 64 34" width="64" height="34" aria-hidden="true">
                <g className={`node ${l.kind} seen`}><rect x="2" y="3" width="60" height="28" rx="4" /></g>
              </svg>
              <div><strong>{l.name}</strong><p>{l.text}</p></div>
            </div>
          ))}
          <div className="legend-item">
            <svg viewBox="0 0 64 34" width="64" height="34" aria-hidden="true">
              <g className="node llm seen runtime"><rect x="2" y="3" width="60" height="28" rx="4" /></g>
            </svg>
            <div><strong>Dashed outline</strong><p>An agent that is created while the program runs.</p></div>
          </div>
          <div className="legend-item">
            <svg viewBox="0 0 64 34" width="64" height="34" aria-hidden="true">
              <defs><marker id="lg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 1 L9 5 L0 9 z" className="arrowhead current" /></marker></defs>
              <g className="edge current"><polyline points="4,17 58,17" markerEnd="url(#lg)" /></g>
            </svg>
            <div><strong>Orange arrow</strong><p>What is moving in the current step.</p></div>
          </div>
        </div>
      </section>

      <section className="wrap section" id="foundations">
        <h2>What all the demos have in common</h2>
        <div className="cols-3">
          <div>
            <h3>Tests decide</h3>
            <p>Generated code runs in a separate process against tests the model never sees. A confident wrong answer still fails.</p>
          </div>
          <div>
            <h3>One small agent</h3>
            <p>An agent is just a name, a persona (the system prompt) and a temperature. The patterns differ in how agents are connected.</p>
          </div>
          <div>
            <h3>A local model</h3>
            <p>Everything runs on a model served by Ollama. Results change from run to run, which is worth comparing in class.</p>
          </div>
        </div>
        <p className="caution">
          <strong>A note on safety.</strong> The sandbox is process-level isolation, fine for a classroom. Use containers before
          running code from a model you don’t trust.
        </p>
      </section>
    </>
  );
}

function Stepper({ pattern }: { pattern: Pattern }) {
  const { steps } = pattern;
  const [i, setI] = useState(() => {
    const n = Number(new URLSearchParams(window.location.hash.split("?")[1] ?? "").get("step"));
    return Number.isInteger(n) && n >= 1 && n <= steps.length ? n - 1 : 0;
  });
  const [playing, setPlaying] = useState(false);
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!playing) return;
    const t = window.setTimeout(() => {
      if (i >= steps.length - 1) setPlaying(false);
      else setI(i + 1);
    }, 5500);
    return () => window.clearTimeout(t);
  }, [playing, i, steps.length]);

  const go = (n: number) => { setPlaying(false); setI(Math.max(0, Math.min(steps.length - 1, n))); };
  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); go(i + 1); }
    if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); go(i - 1); }
  };

  const step = steps[i];
  return (
    <div className="stepper" ref={root} onKeyDown={onKey}>
      <ol className="step-list" aria-label="Steps">
        {steps.map((s, n) => (
          <li key={n}>
            <button className={n === i ? "on" : n < i ? "past" : ""} onClick={() => go(n)} aria-current={n === i ? "step" : undefined}>
              <span className="step-num">{n + 1}</span>
              <span className="step-title">{s.title}</span>
            </button>
          </li>
        ))}
      </ol>

      <div className="stage">
        <Diagram diagram={pattern.diagram} steps={steps} current={i} />
        <StepDetail step={step} index={i} total={steps.length} />
        <div className="controls">
          <button onClick={() => go(i - 1)} disabled={i === 0}>Previous</button>
          <button onClick={() => (i >= steps.length - 1 ? go(0) : go(i + 1))} className="primary">
            {i >= steps.length - 1 ? "Restart" : "Next"}
          </button>
          <button onClick={() => { if (!playing && i >= steps.length - 1) setI(0); setPlaying(!playing); }}>
            {playing ? "Pause" : "Auto-play"}
          </button>
          <span className="hint">Arrow keys also work</span>
        </div>
      </div>
    </div>
  );
}

function StepDetail({ step, index, total }: { step: Step; index: number; total: number }) {
  return (
    <div className="detail" aria-live="polite">
      <div className="detail-main">
        <div className="detail-meta">
          <span>Step {index + 1} of {total}</span>
          <span className={`actor ${step.actor.toLowerCase().replace(/\s+/g, "-")}`}>{step.actor}</span>
        </div>
        <h3>{step.title}</h3>
        <p>{step.body}</p>
        {step.points && <ul>{step.points.map((p) => <li key={p}>{p}</li>)}</ul>}
      </div>
      {(step.artifact || step.matrix || step.path) && (
        <div className="detail-artifact">
          {step.artifact && (
            <figure>
              <figcaption>{step.artifact.label}</figcaption>
              <pre className={step.artifact.kind}>{step.artifact.body}</pre>
            </figure>
          )}
          {step.matrix && (
            <figure>
              <figcaption>{step.matrix.caption}</figcaption>
              <div className="table-scroll">
                <table className="matrix">
                  <thead><tr>{step.matrix.head.map((h) => <th key={h}>{h}</th>)}</tr></thead>
                  <tbody>
                    {step.matrix.rows.map((r, ri) => (
                      <tr key={ri}>
                        {r.map((c, ci) => (
                          <td key={ci} className={ci === 0 ? "rowhead" : `g${step.matrix!.group[ci - 1]}`}>{c}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="matrix-key"><span className="g0">Group 1</span><span className="g1">Group 2</span></div>
            </figure>
          )}
          {step.path && (
            <figure>
              <figcaption>{step.path[0].note ?? ""}</figcaption>
              {step.path.map((p) => (
                <div key={p.label} className="path">
                  <div className="path-label">{p.label}</div>
                  <div className="path-chips">
                    {p.steps.map((s, k) => (
                      <span key={k} className="chip-wrap"><span className={`chip c-${s}`}>{s}</span>{k < p.steps.length - 1 && <i>›</i>}</span>
                    ))}
                  </div>
                </div>
              ))}
            </figure>
          )}
        </div>
      )}
    </div>
  );
}

function PatternPage({ pattern }: { pattern: Pattern }) {
  const idx = PATTERNS.findIndex((p) => p.id === pattern.id);
  const prev = PATTERNS[idx - 1];
  const next = PATTERNS[idx + 1];
  return (
    <>
      <section className="pattern-head">
        <div className="wrap">
          <p className="eyebrow">{pattern.code} · {pattern.group}</p>
          <h1>{pattern.title}</h1>
          <p className="lede">{pattern.scenario}.</p>
        </div>
      </section>

      <section className="wrap section tight">
        <div className="descr">
          <div className="descr-row"><h2 className="small">Context</h2><p>{pattern.context}</p></div>
          <div className="descr-row"><h2 className="small">Problem</h2><p>{pattern.problem}</p></div>
          <div className="descr-row"><h2 className="small">Solution</h2><p>{pattern.solution}</p></div>
          <div className="descr-row">
            <h2 className="small">Use when</h2>
            <ul className="plain">{pattern.useWhen.map((t) => <li key={t}>{t}</li>)}</ul>
          </div>
          <div className="descr-row"><h2 className="small">Trade-off</h2><p>{pattern.tradeoff}</p></div>
        </div>
        <dl className="facts">
          <div><dt>LLM calls</dt><dd>{pattern.llmCalls}</dd></div>
          <div><dt>Result checked by</dt><dd>{pattern.verifiedBy}</dd></div>
          <div><dt>Demo tasks</dt><dd><code>{pattern.task}</code></dd></div>
        </dl>
      </section>

      <section className="wrap section" id="how">
        <h2>How it works, step by step</h2>
        <Stepper key={pattern.id} pattern={pattern} />
      </section>

      <section className="wrap section" id="sequence">
        <h2>Sequence diagram</h2>
        <p className="section-intro">
          The same pattern as messages between components, in order. Solid arrows are calls and dashed arrows are replies.
          Boxes mark loops and parallel work.
        </p>
        <SequenceDiagram seq={SEQUENCES[pattern.code]} id={pattern.id} />
      </section>

      <section className="wrap section">
        <h2>Pros and cons</h2>
        <div className="proscons">
          {(["pro", "con"] as const).map((kind) => (
            <div key={kind} className={`pc ${kind}`}>
              <h3>{kind === "pro" ? "Pros" : "Cons"}</h3>
              <ul>
                {pattern.consequences.filter((c) => c.effect === kind).map((c) => (
                  <li key={c.attribute + c.text}><strong>{c.attribute}</strong>{c.text}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="wrap section">
        <h2>Run it</h2>
        <pre className="cmd">{pattern.run}</pre>
        <p className="muted small-text">Or launch the Streamlit app with <code>./run.sh</code> and choose this pattern in the sidebar. Requires a local Ollama model.</p>
        <table className="files">
          <tbody>
            {pattern.files.map((f) => (
              <tr key={f.path}><td><code>{f.path}</code></td><td className="muted">{f.what}</td></tr>
            ))}
          </tbody>
        </table>
      </section>

      <nav className="wrap pager" aria-label="Pattern navigation">
        {prev ? <a href={`#/${prev.id}`}><small>Previous</small>{prev.code} · {prev.title}</a> : <span />}
        {next ? <a href={`#/${next.id}`} className="right"><small>Next</small>{next.code} · {next.title}</a> : <a href="#/" className="right"><small>Back to</small>All patterns</a>}
      </nav>
    </>
  );
}

export default function App() {
  const route = useRoute();
  const pattern = PATTERNS.find((p) => p.id === route.split("?")[0]);
  useEffect(() => {
    document.title = pattern ? `${pattern.title} · AutoSE Agent Patterns` : "AutoSE Agent Patterns";
  }, [pattern]);
  return (
    <>
      <Header />
      <main>{pattern ? <PatternPage pattern={pattern} /> : <Home />}</main>
      <Footer />
    </>
  );
}
