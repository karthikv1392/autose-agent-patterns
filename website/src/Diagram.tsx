import { useMemo } from "react";
import type { Diagram as D, Edge, Node, Side, Step } from "./data";

type Pt = [number, number];

function anchor(n: Node, s: Side, off = 0): Pt {
  switch (s) {
    case "r": return [n.x + n.w, n.y + n.h / 2 + off];
    case "l": return [n.x, n.y + n.h / 2 + off];
    case "t": return [n.x + n.w / 2 + off, n.y];
    default: return [n.x + n.w / 2 + off, n.y + n.h];
  }
}

function inferSides(a: Node, b: Node): [Side, Side] {
  if (b.x >= a.x + a.w - 1) return ["r", "l"];
  if (b.x + b.w <= a.x + 1) return ["l", "r"];
  return b.y > a.y ? ["b", "t"] : ["t", "b"];
}

function route(e: Edge, nodes: Map<string, Node>): Pt[] {
  if (e.pts) return e.pts;
  const a = nodes.get(e.from)!;
  const b = nodes.get(e.to)!;
  const [fs, ts] = [e.fs, e.ts].every(Boolean) ? [e.fs!, e.ts!] : inferSides(a, b);
  const p = anchor(a, fs, e.fOff);
  const q = anchor(b, ts, e.tOff);
  const horizontal = fs === "r" || fs === "l";
  if (horizontal && Math.abs(p[1] - q[1]) < 1) return [p, q];
  if (!horizontal && Math.abs(p[0] - q[0]) < 1) return [p, q];
  if (horizontal) {
    const m = e.mid ?? (p[0] + q[0]) / 2;
    return [p, [m, p[1]], [m, q[1]], q];
  }
  const m = e.mid ?? (p[1] + q[1]) / 2;
  return [p, [p[0], m], [q[0], m], q];
}

// Label sits on the longest segment, nudged off the line so it does not hide the arrow tip.
function labelAt(pts: Pt[]): Pt {
  let best = 0, bi = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    const len = Math.abs(pts[i + 1][0] - pts[i][0]) + Math.abs(pts[i + 1][1] - pts[i][1]);
    if (len > best) { best = len; bi = i; }
  }
  return [(pts[bi][0] + pts[bi + 1][0]) / 2, (pts[bi][1] + pts[bi + 1][1]) / 2];
}

type State = "current" | "seen" | "future";

export default function Diagram({ diagram, steps, current }: { diagram: D; steps: Step[]; current: number }) {
  const nodeMap = useMemo(() => new Map(diagram.nodes.map((n) => [n.id, n])), [diagram]);

  // First step in which each node / edge is active. Drives the number badges and fading.
  const firstNode = useMemo(() => {
    const m = new Map<string, number>();
    steps.forEach((s, i) => s.nodes.forEach((id) => { if (!m.has(id)) m.set(id, i); }));
    return m;
  }, [steps]);
  const firstEdge = useMemo(() => {
    const m = new Map<string, number>();
    steps.forEach((s, i) => (s.edges ?? []).forEach((id) => { if (!m.has(id)) m.set(id, i); }));
    return m;
  }, [steps]);

  const nodeState = (id: string): State => {
    if (steps[current].nodes.includes(id)) return "current";
    const f = firstNode.get(id);
    return f !== undefined && f < current ? "seen" : "future";
  };
  const edgeState = (id: string): State => {
    if ((steps[current].edges ?? []).includes(id)) return "current";
    const f = firstEdge.get(id);
    return f !== undefined && f < current ? "seen" : "future";
  };

  return (
    <div className="diagram-scroll">
      <svg
        className="diagram"
        viewBox={`0 0 960 ${diagram.height}`}
        role="img"
        aria-label={`Diagram, step ${current + 1} of ${steps.length}: ${steps[current].title}`}
      >
        <defs>
          {(["current", "seen", "future"] as State[]).map((s) => (
            <marker key={s} id={`arrow-${s}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
              <path d="M0 1 L9 5 L0 9 z" className={`arrowhead ${s}`} />
            </marker>
          ))}
        </defs>

        {diagram.groups?.map((g) => (
          <g key={g.label} className="group">
            <rect x={g.x} y={g.y} width={g.w} height={g.h} rx="4" />
            <text x={g.x + 10} y={g.y + 17} className="group-label">{g.label}</text>
          </g>
        ))}

        {diagram.edges.map((e) => {
          const pts = route(e, nodeMap);
          const st = edgeState(e.id);
          const [lx, ly] = labelAt(pts);
          const horizontalSeg = pts.length > 1 && pts.some((p, i) => i > 0 && p[1] === pts[i - 1][1] && p[0] !== pts[i - 1][0]);
          return (
            <g key={e.id} className={`edge ${st}${e.dashed ? " dashed" : ""}`}>
              <polyline points={pts.map((p) => p.join(",")).join(" ")} markerEnd={`url(#arrow-${st})`} markerStart={e.both ? `url(#arrow-${st})` : undefined} />
              {e.label && (
                <g className="edge-label" transform={`translate(${lx + (horizontalSeg ? 0 : (e.label.length * 3.1 + 11) * (e.labelLeft ? -1 : 1))} ${ly + (horizontalSeg ? -9 : 0)})`}>
                  <rect x={-(e.label.length * 3.1 + 5)} y={-9} width={e.label.length * 6.2 + 10} height={16} rx="2" />
                  <text textAnchor="middle" y={3}>{e.label}</text>
                </g>
              )}
            </g>
          );
        })}

        {diagram.nodes.map((n) => {
          const st = nodeState(n.id);
          const lines = [
            ...n.label.split("\n").map((t) => ({ t, c: "node-label", h: 16 })),
            ...(n.sub ? n.sub.split("\n") : []).map((t) => ({ t, c: "node-sub", h: 14 })),
          ];
          let cy = n.y + n.h / 2 - lines.reduce((a, l) => a + l.h, 0) / 2;
          const badge = firstNode.get(n.id);
          return (
            <g key={n.id} className={`node ${n.kind} ${st}${n.runtime ? " runtime" : ""}`}>
              <rect x={n.x} y={n.y} width={n.w} height={n.h} rx="4" />
              {lines.map((l, i) => {
                const y = cy + l.h * 0.78;
                cy += l.h;
                return <text key={i} x={n.x + n.w / 2} y={y} className={l.c} textAnchor="middle">{l.t}</text>;
              })}
              {badge !== undefined && (
                <g className="badge" transform={`translate(${n.x} ${n.y})`}>
                  <circle r="10" />
                  <text y="3.5" textAnchor="middle">{badge + 1}</text>
                </g>
              )}
            </g>
          );
        })}

        {diagram.notes?.map((t) => (
          <text key={t.text} x={t.x} y={t.y} textAnchor={t.anchor ?? "start"} className="note">{t.text}</text>
        ))}
      </svg>
    </div>
  );
}
