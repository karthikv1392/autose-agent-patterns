"""AutoSE Agent Patterns — Streamlit UI.

Run:  streamlit run app.py      (or ./run.sh)
Every pattern writes to a Trace; this file only decides how to draw trace events.
"""

import streamlit as st

from patterns.registry import PATTERNS, load
from shared import llm
from shared.tasks import load_task
from shared.trace import Event, Trace

st.set_page_config(page_title="AutoSE Agent Patterns", page_icon="🛠️", layout="wide")

# ── Sidebar ──────────────────────────────────────────────────────────────
st.sidebar.title("🛠️ AutoSE Agent Patterns")
st.sidebar.caption("Agentic patterns applied to autonomous software engineering.")

try:
    import ollama
    installed = [m.model for m in ollama.list().models if "embed" not in m.model]
except Exception:
    installed = []
default_idx = next((i for i, m in enumerate(installed) if m.split(":")[0] == llm.MODEL.split(":")[0]), 0)
model = st.sidebar.selectbox("Local model (Ollama)", installed or [llm.MODEL], index=default_idx if installed else 0)
llm.set_model(model)
if not installed:
    st.sidebar.warning("Could not reach Ollama. Start it with `ollama serve`.")

labels = {f"{p['group']} · {p['title']}": p for p in PATTERNS}
choice = st.sidebar.radio("Pattern", list(labels))
pattern = labels[choice]
module = load(pattern["id"])

# ── Header ───────────────────────────────────────────────────────────────
st.title(pattern["title"])
st.markdown(f"**{pattern['group']}** — {pattern['tagline']}")
with st.expander("How it works (diagram and rationale)", expanded=True):
    st.code(module.__doc__.strip(), language="text")
st.caption(f"Code: `patterns/{pattern['id']}/` · Generic version of this pattern: `{pattern['original']}` in the Agentic_Patterns repo")

# ── Task picker ──────────────────────────────────────────────────────────
task_key = st.selectbox("Software-engineering task", pattern["tasks"],
                        format_func=lambda k: f"{load_task(k).title}  [{load_task(k).kind}]")
task = load_task(task_key)
st.info(task.summary)

col1, col2 = st.columns(2)
with col1:
    with st.expander("Task description given to the agent"):
        st.markdown(task.spec)
with col2:
    with st.expander("Starting code and tests (ground truth)"):
        for name, src in task.starter.items():
            st.caption(name)
            st.code(src, language="python")
        st.caption("test_suite.py — the agents are judged by running this")
        st.code(task.tests, language="python")

options = {}
if pattern["options"]:
    cols = st.columns(len(pattern["options"]))
    for col, o in zip(cols, pattern["options"]):
        options[o["key"]] = col.slider(o["label"], o["min"], o["max"], o["default"])

# ── Live trace rendering ─────────────────────────────────────────────────
def make_renderer(box):
    def render(e: Event):
        who = f"**{e.agent}** · " if e.agent else ""
        if e.kind == "step":
            box.markdown(f"#### {e.title}")
        elif e.kind == "text":
            with box.expander(f"{e.agent or ''} — {e.title}".strip(" —"), expanded=True):
                st.markdown(e.body)
        elif e.kind == "code":
            with box.expander(f"{e.agent or ''} — {e.title}".strip(" —"), expanded=e.lang != "json"):
                st.code(e.body or "(empty)", language=e.lang or "python")
        elif e.kind == "tests":
            (box.success if e.ok else box.error)(f"{who}{e.title}")
            with box.expander("Test output"):
                st.code(e.body, language="text")
        elif e.kind == "table":
            box.markdown(f"{who}{e.title}")
            box.dataframe(e.data, use_container_width=True, hide_index=True)
    return render


def show_result(result):
    st.divider()
    (st.success if result["solved"] else st.warning)(result["headline"])
    c1, c2 = st.columns(2)
    c1.metric("Tests", result["report"].summary() if result.get("report") else "—")
    c2.metric("LLM-backed", model)
    with st.expander("Final code produced"):
        for name, src in result["files"].items():
            st.caption(name)
            st.code(src, language="python")


def interactive_flow():
    """Patterns with a human decision in the middle: plan, let the person decide, then execute."""
    key = (pattern["id"], task_key, tuple(sorted(options.items())))
    render = make_renderer(st.container())
    if st.button("▶ Plan and classify", type="primary"):
        trace = Trace()
        with st.spinner("Planning and scoring the risk of each action…"):
            state = module.plan(task_key, trace=trace, **options)
        st.session_state["review"] = {"key": key, "state": state, "events": trace.events, "id": id(state)}
        st.session_state.pop("review_result", None)
        st.rerun()

    review = st.session_state.get("review")
    if not review or review["key"] != key:
        return
    for e in review["events"]:
        render(e)

    st.divider()
    st.subheader("Human review")
    high = [a for a in review["state"]["actions"] if a["approval_required"]]
    approver = st.text_input("Your name (recorded in the audit trail)", "reviewer", key=f"who{review['id']}")
    decisions = {}
    for a in high:
        with st.container(border=True):
            st.markdown(f"**Action {a['index']} · risk {a['risk_score']}/10** — {a['action']}")
            st.caption(f"{a['reversibility']} · scope {a['impact_scope']} · {a['reasoning']}")
            choice = st.radio("Decision", ["Reject", "Approve"], horizontal=True, key=f"d{review['id']}{a['index']}")
            note = st.text_input("Note (optional)", key=f"n{review['id']}{a['index']}")
            decisions[a["index"]] = {"status": "approved" if choice == "Approve" else "rejected",
                                     "approver": approver, "notes": note}
    if not high:
        st.info("No action needs approval, so everything can run.")
    st.caption("Anything left on Reject, or without a decision, is skipped.")

    if st.button("▶ Execute with these decisions", type="primary"):
        box = st.container()
        with st.spinner("Executing the allowed actions…"):
            st.session_state["review_result"] = module.execute(review["state"], decisions, trace=Trace(on_event=make_renderer(box)))
    if "review_result" in st.session_state:
        show_result(st.session_state["review_result"])


if pattern.get("interactive"):
    interactive_flow()
elif st.button("▶ Run pattern", type="primary"):
    box = st.container()
    trace = Trace(on_event=make_renderer(box))
    with st.spinner("Agents working… (local models can take a few minutes)"):
        result = module.run(task_key, trace=trace, **options)
    show_result(result)
