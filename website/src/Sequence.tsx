import type { Sequence } from "./sequences";

const ROW = 64;
const TOP = 96;

export default function SequenceDiagram({ seq, id }: { seq: Sequence; id: string }) {
  const { participants: ps, messages, fragments = [] } = seq;
  const width = Math.max(860, ps.length * 200);
  const margin = 120;
  const gap = ps.length > 1 ? (width - margin * 2) / (ps.length - 1) : 0;
  const xs = ps.map((_, i) => margin + gap * i);
  const height = TOP + messages.length * ROW + 70;
  const y = (i: number) => TOP + i * ROW;
  const arrow = `seq-arrow-${id}`;

  const head = (i: number, bottom?: boolean) => {
    const p = ps[i];
    const lines = p.name.length > 20 ? wrap(p.name) : [p.name];
    const yy = bottom ? height - 52 : 12;
    return (
      <g className={`seq-part ${p.kind}`} key={`${i}${bottom ? "b" : "t"}`}>
        <rect x={xs[i] - 90} y={yy} width="180" height="40" rx="3" />
        {lines.map((l, k) => (
          <text key={k} className={k ? "sub" : ""} x={xs[i]} y={yy + (lines.length === 1 ? 25 : 17 + k * 14)} textAnchor="middle">{l}</text>
        ))}
      </g>
    );
  };

  return (
    <div className="diagram-scroll seq-scroll">
      <svg className="seq" viewBox={`0 0 ${width} ${height}`} style={{ minWidth: 820 }} role="img"
        aria-label={messages.map((m) => `${ps[m.from].name} to ${ps[m.to].name}: ${m.label}`).join(". ")}>
        <defs>
          <marker id={arrow} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0 0 L10 5 L0 10 z" className="seq-head" />
          </marker>
        </defs>

        {fragments.map((f) => {
          const y1 = y(f.start) - 48, y2 = y(f.end) + 24;
          const w = Math.min(f.label.length * 6.6 + 18, width - 20);
          return (
            <g className="seq-frag" key={f.label}>
              <rect x={14} y={y1} width={width - 28} height={y2 - y1} rx="3" />
              <rect className="tab" x={14} y={y1} width={w} height="18" />
              <text x={22} y={y1 + 13}>{f.label}</text>
            </g>
          );
        })}

        {ps.map((_, i) => <line key={i} className="lifeline" x1={xs[i]} y1="52" x2={xs[i]} y2={height - 52} />)}
        {ps.map((_, i) => head(i))}
        {ps.map((_, i) => head(i, true))}

        {messages.map((m, i) => {
          const x1 = xs[m.from], x2 = xs[m.to], yy = y(i);
          const self = m.from === m.to;
          const tx = self ? x1 + 70 : (x1 + x2) / 2;
          const tw = m.label.length * 6.1 + 12;
          return (
            <g key={i} className={`seq-msg ${m.reply ? "reply" : "call"}`}>
              {self ? (
                <>
                  <path d={`M${x1} ${yy} H${x1 + 44} V${yy + 22} H${x1 + 4}`} markerEnd={`url(#${arrow})`} />
                  {x1 + 52 + tw > width - 10 ? (
                    <>
                      <rect className="lbl" x={x1 - 12 - tw} y={yy - 3} width={tw} height="16" />
                      <text x={x1 - 18} y={yy + 9} textAnchor="end">{m.label}</text>
                    </>
                  ) : (
                    <>
                      <rect className="lbl" x={x1 + 52} y={yy - 3} width={tw} height="16" />
                      <text x={x1 + 58} y={yy + 9}>{m.label}</text>
                    </>
                  )}
                </>
              ) : (
                <>
                  <line x1={x1} y1={yy} x2={x2} y2={yy} markerEnd={`url(#${arrow})`} />
                  <rect className="lbl" x={tx - tw / 2} y={yy - 21} width={tw} height="16" />
                  <text x={tx} y={yy - 9} textAnchor="middle">{m.label}</text>
                </>
              )}
              <text className="seq-n" x={40} y={yy + 4} textAnchor="end">{i + 1}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function wrap(s: string): string[] {
  const i = s.indexOf(" (");
  return i > 0 ? [s.slice(0, i), s.slice(i + 1)] : [s];
}
