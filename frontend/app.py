import streamlit as st
import uuid
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pipeline import run_pipeline
from agents.agent5_feedback_learner import record_user_interaction
from storage.feedback_store import init_db

init_db()

st.set_page_config(
    page_title="PubMed AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* ── global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background: #0f1117; }

    /* ── hero header ── */
    .hero-container {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 50%, #0f3460 100%);
        border: 1px solid #2d3561;
        border-radius: 16px;
        padding: 40px;
        margin-bottom: 28px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(99,179,237,0.05) 0%, transparent 60%);
        pointer-events: none;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #63b3ed, #9f7aea, #63b3ed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 8px 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        color: #8892a4;
        font-size: 1.05rem;
        font-weight: 400;
        margin: 0;
    }
    .hero-badges {
        margin-top: 16px;
        display: flex;
        gap: 10px;
        justify-content: center;
        flex-wrap: wrap;
    }
    .badge {
        background: rgba(99,179,237,0.1);
        border: 1px solid rgba(99,179,237,0.3);
        color: #63b3ed;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    /* ── pipeline step tracker ── */
    .pipeline-container {
        background: #1a1f2e;
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    .pipeline-title {
        color: #8892a4;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 16px;
    }
    .steps-row {
        display: flex;
        align-items: center;
        gap: 0;
    }
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }
    .step-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 600;
        border: 2px solid #2d3561;
        background: #0f1117;
        color: #4a5568;
        transition: all 0.3s;
        z-index: 2;
    }
    .step-circle.active {
        border-color: #63b3ed;
        background: rgba(99,179,237,0.15);
        color: #63b3ed;
        box-shadow: 0 0 16px rgba(99,179,237,0.3);
    }
    .step-circle.done {
        border-color: #48bb78;
        background: rgba(72,187,120,0.15);
        color: #48bb78;
    }
    .step-circle.error {
        border-color: #fc8181;
        background: rgba(252,129,129,0.15);
        color: #fc8181;
    }
    .step-label {
        font-size: 0.65rem;
        color: #4a5568;
        margin-top: 6px;
        text-align: center;
        font-weight: 500;
        white-space: nowrap;
    }
    .step-label.active { color: #63b3ed; }
    .step-label.done { color: #48bb78; }
    .step-connector {
        flex: 1;
        height: 2px;
        background: #2d3561;
        margin-top: -20px;
        z-index: 1;
    }
    .step-connector.done { background: #48bb78; }

    /* ── timing pills ── */
    .timing-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 12px;
    }
    .timing-pill {
        background: rgba(99,179,237,0.08);
        border: 1px solid rgba(99,179,237,0.2);
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.7rem;
        color: #8892a4;
        font-family: 'JetBrains Mono', monospace;
    }
    .timing-pill span { color: #63b3ed; font-weight: 500; }

    /* ── pico card ── */
    .pico-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-top: 12px;
    }
    .pico-item {
        background: #0f1117;
        border: 1px solid #2d3561;
        border-radius: 10px;
        padding: 14px 16px;
    }
    .pico-label {
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .pico-value {
        font-size: 0.9rem;
        color: #e2e8f0;
        font-weight: 400;
    }
    .pico-P .pico-label { color: #63b3ed; }
    .pico-I .pico-label { color: #9f7aea; }
    .pico-C .pico-label { color: #f6ad55; }
    .pico-O .pico-label { color: #68d391; }

    /* ── query box ── */
    .query-box {
        background: #0f1117;
        border: 1px solid #2d3561;
        border-radius: 10px;
        padding: 14px 16px;
        margin-top: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #63b3ed;
        line-height: 1.6;
        word-break: break-all;
    }

    /* ── mesh tags ── */
    .mesh-container {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 10px;
    }
    .mesh-tag {
        background: rgba(159,122,234,0.1);
        border: 1px solid rgba(159,122,234,0.3);
        color: #9f7aea;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 500;
    }

    /* ── paper card ── */
    .paper-card {
        background: #1a1f2e;
        border: 1px solid #2d3561;
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 16px;
        transition: border-color 0.2s;
        position: relative;
    }
    .paper-card:hover { border-color: #4a5568; }
    .paper-card.relevant { border-color: #48bb78; border-left: 4px solid #48bb78; }
    .paper-card.irrelevant { border-color: #fc8181; border-left: 4px solid #fc8181; }

    .paper-rank {
        position: absolute;
        top: 16px;
        right: 16px;
        background: rgba(99,179,237,0.1);
        border: 1px solid rgba(99,179,237,0.2);
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 0.7rem;
        color: #63b3ed;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
    }
    .paper-title {
        font-size: 1.0rem;
        font-weight: 600;
        color: #e2e8f0;
        margin: 0 0 6px 0;
        padding-right: 80px;
        line-height: 1.4;
    }
    .paper-meta {
        font-size: 0.78rem;
        color: #8892a4;
        margin-bottom: 14px;
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
    }
    .paper-meta span { display: flex; align-items: center; gap: 4px; }

    .highlight-box {
        background: rgba(246,173,85,0.08);
        border-left: 3px solid #f6ad55;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.85rem;
        color: #e2e8f0;
        line-height: 1.6;
        font-style: italic;
    }
    .no-highlight {
        font-size: 0.82rem;
        color: #4a5568;
        font-style: italic;
    }

    /* ── score bar ── */
    .score-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 14px;
    }
    .score-label {
        font-size: 0.68rem;
        color: #8892a4;
        white-space: nowrap;
        font-weight: 500;
    }
    .score-bar-bg {
        flex: 1;
        height: 5px;
        background: #2d3561;
        border-radius: 3px;
        overflow: hidden;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #63b3ed, #9f7aea);
    }
    .score-value {
        font-size: 0.7rem;
        color: #63b3ed;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        min-width: 36px;
        text-align: right;
    }

    /* ── sidebar ── */
    .sidebar-section {
        background: #1a1f2e;
        border: 1px solid #2d3561;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 14px;
    }
    .sidebar-title {
        font-size: 0.68rem;
        font-weight: 700;
        color: #8892a4;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0;
        border-bottom: 1px solid #2d3561;
        font-size: 0.82rem;
    }
    .stat-row:last-child { border-bottom: none; }
    .stat-label { color: #8892a4; }
    .stat-value { color: #63b3ed; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

    .history-item {
        padding: 8px 0;
        border-bottom: 1px solid #2d3561;
        font-size: 0.8rem;
        color: #8892a4;
        cursor: pointer;
    }
    .history-item:hover { color: #63b3ed; }
    .history-item:last-child { border-bottom: none; }
    .history-num {
        font-size: 0.65rem;
        color: #4a5568;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── feedback buttons ── */
    .stButton > button {
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }

    /* ── empty state ── */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #4a5568;
    }
    .empty-icon { font-size: 3rem; margin-bottom: 16px; }
    .empty-title { font-size: 1.1rem; color: #8892a4; margin-bottom: 8px; font-weight: 500; }
    .empty-subtitle { font-size: 0.85rem; }

    /* ── section label ── */
    .section-label {
        font-size: 0.68rem;
        font-weight: 700;
        color: #8892a4;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin: 20px 0 10px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-label::after {
        content: '';
        flex: 1;
        height: 1px;
        background: #2d3561;
    }

    /* hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── session state init ──────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "results" not in st.session_state:
    st.session_state.results = None
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "interactions" not in st.session_state:
    st.session_state.interactions = {}
if "is_searching" not in st.session_state:
    st.session_state.is_searching = False
if "pipeline_steps" not in st.session_state:
    st.session_state.pipeline_steps = {}
if "current_query" not in st.session_state:
    st.session_state.current_query = ""


# ── sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 16px 0 20px;'>
        <div style='font-size:2rem; margin-bottom:8px;'>🔬</div>
        <div style='font-size:0.95rem; font-weight:600; color:#e2e8f0;'>PubMed AI</div>
        <div style='font-size:0.72rem; color:#4a5568; margin-top:4px;'>Research Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    # session info
    st.markdown(f"""
    <div class='sidebar-section'>
        <div class='sidebar-title'>Session</div>
        <div class='stat-row'>
            <span class='stat-label'>Session ID</span>
            <span class='stat-value'>#{st.session_state.session_id}</span>
        </div>
        <div class='stat-row'>
            <span class='stat-label'>Searches</span>
            <span class='stat-value'>{len(st.session_state.query_history)}</span>
        </div>
        <div class='stat-row'>
            <span class='stat-label'>Relevant</span>
            <span class='stat-value' style='color:#48bb78'>{sum(1 for v in st.session_state.interactions.values() if v == 'relevant')}</span>
        </div>
        <div class='stat-row'>
            <span class='stat-label'>Not Relevant</span>
            <span class='stat-value' style='color:#fc8181'>{sum(1 for v in st.session_state.interactions.values() if v == 'irrelevant')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # query history
    if st.session_state.query_history:
        st.markdown("""
        <div class='sidebar-section'>
            <div class='sidebar-title'>Recent Searches</div>
        """, unsafe_allow_html=True)
        for i, q in enumerate(reversed(st.session_state.query_history[-5:])):
            st.markdown(f"""
            <div class='history-item'>
                <div class='history-num'>#{len(st.session_state.query_history) - i}</div>
                <div>{q[:45]}{'...' if len(q) > 45 else ''}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # pipeline info
    st.markdown("""
    <div class='sidebar-section'>
        <div class='sidebar-title'>Pipeline Agents</div>
        <div class='stat-row'><span class='stat-label'>🧠 Agent 1</span><span class='stat-value' style='color:#8892a4;font-size:0.65rem'>PICO Extractor</span></div>
        <div class='stat-row'><span class='stat-label'>🏷️ Agent 2</span><span class='stat-value' style='color:#8892a4;font-size:0.65rem'>MeSH Translator</span></div>
        <div class='stat-row'><span class='stat-label'>🔧 Agent 3</span><span class='stat-value' style='color:#8892a4;font-size:0.65rem'>Query Builder</span></div>
        <div class='stat-row'><span class='stat-label'>🔍 Agent 4</span><span class='stat-value' style='color:#8892a4;font-size:0.65rem'>PubMed Finder</span></div>
        <div class='stat-row'><span class='stat-label'>📈 Agent 5</span><span class='stat-value' style='color:#8892a4;font-size:0.65rem'>Feedback Learner</span></div>
    </div>
    """, unsafe_allow_html=True)


# ── main content ────────────────────────────────────────────────
st.markdown("""
<div class='hero-container'>
    <div class='hero-title'>PubMed AI Research Assistant</div>
    <div class='hero-subtitle'>Ask any medical question in plain English — get ranked, annotated research papers</div>
    <div class='hero-badges'>
        <span class='badge'>5 AI Agents</span>
        <span class='badge'>30M+ Papers</span>
        <span class='badge'>RAG Ranking</span>
        <span class='badge'>MeSH Translation</span>
        <span class='badge'>Feedback Learning</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── search bar ──────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_input(
        label="query",
        placeholder="e.g. Does exercise help depressed teenagers? Is aspirin better than ibuprofen for headaches?",
        label_visibility="collapsed",
        key="query_input"
    )
with col_btn:
    search_clicked = st.button("🔍 Search", use_container_width=True, type="primary")

example_cols = st.columns(4)
examples = [
    "Does exercise help depressed teenagers?",
    "Is aspirin effective for headaches?",
    "Does walking reduce back pain?",
    "Can meditation reduce anxiety?"
]
for i, (col, ex) in enumerate(zip(example_cols, examples)):
    with col:
        if st.button(ex[:30] + "...", key=f"ex_{i}", use_container_width=True):
            query = ex
            search_clicked = True


# ── pipeline runner ─────────────────────────────────────────────
def render_pipeline_tracker(steps: dict):
    step_defs = [
        ("1", "PICO\nExtract", "agent1"),
        ("2", "MeSH\nTranslate", "agent2"),
        ("3", "Query\nBuild", "agent3"),
        ("4", "PubMed\nSearch", "agent4"),
        ("5", "Rank &\nHighlight", "agent5_rank"),
    ]

    circles = ""
    for i, (num, label, key) in enumerate(step_defs):
        state = steps.get(key, "pending")
        icon = {"done": "✓", "active": "⟳", "error": "✗", "pending": num}[state]
        circles += f"<div class='step-item'><div class='step-circle {state}'>{icon}</div><div class='step-label {state}'>{label.replace(chr(10), ' ')}</div></div>"
        if i < len(step_defs) - 1:
            conn_class = "done" if steps.get(key) == "done" else ""
            circles += f"<div class='step-connector {conn_class}'></div>"

    st.markdown(f"""
    <div class='pipeline-container'>
        <div class='pipeline-title'>⚡ Pipeline Progress</div>
        <div class='steps-row'>{circles}</div>
    </div>
    """, unsafe_allow_html=True)


if search_clicked and query.strip():
    st.session_state.current_query = query.strip()
    if query.strip() not in st.session_state.query_history:
        st.session_state.query_history.append(query.strip())

    steps = {}
    pipeline_placeholder = st.empty()
    status_placeholder = st.empty()

    with st.spinner(""):
        # show initial tracker
        with pipeline_placeholder.container():
            render_pipeline_tracker(steps)

        status_placeholder.info("🧠 **Agent 1** — Extracting PICO components from your question...")
        steps["agent1"] = "active"
        with pipeline_placeholder.container():
            render_pipeline_tracker(steps)

        try:
            t_start = time.time()
            result = run_pipeline(query.strip())
            t_total = round(time.time() - t_start, 1)

            if result.success:
                steps = {
                    "agent1": "done",
                    "agent2": "done",
                    "agent3": "done",
                    "agent4": "done",
                    "agent5_rank": "done"
                }
            else:
                failed = result.failed_at_agent or ""
                if "1" in failed:
                    steps = {"agent1": "error"}
                elif "2" in failed:
                    steps = {"agent1": "done", "agent2": "error"}
                elif "3" in failed:
                    steps = {"agent1": "done", "agent2": "done", "agent3": "error"}
                elif "4" in failed:
                    steps = {"agent1": "done", "agent2": "done", "agent3": "done", "agent4": "error"}

            with pipeline_placeholder.container():
                render_pipeline_tracker(steps)

            st.session_state.pipeline_result = result
            st.session_state.results = result.papers
            st.session_state.interactions = {}
            status_placeholder.empty()

        except Exception as e:
            steps["agent1"] = "error"
            with pipeline_placeholder.container():
                render_pipeline_tracker(steps)
            status_placeholder.error(f"Pipeline error: {str(e)}")
            st.stop()


# ── results area ────────────────────────────────────────────────
pr = st.session_state.pipeline_result

if pr is None:
    st.markdown("""
    <div class='empty-state'>
        <div class='empty-icon'>🔬</div>
        <div class='empty-title'>Ready to search 30 million medical papers</div>
        <div class='empty-subtitle'>Type your question above or click an example to get started</div>
    </div>
    """, unsafe_allow_html=True)

elif not pr.success:
    st.error(f"**Pipeline failed** at {pr.failed_at_agent}")
    st.code(pr.error_message)

else:
    # ── timing strip ────────────────────────────────────────────
    st.markdown(f"""
    <div class='timing-row'>
        <div class='timing-pill'>Total <span>{pr.timing.total_seconds}s</span></div>
        <div class='timing-pill'>Agent 1 <span>{pr.timing.agent1_seconds}s</span></div>
        <div class='timing-pill'>Agent 2 <span>{pr.timing.agent2_seconds}s</span></div>
        <div class='timing-pill'>Agent 3 <span>{pr.timing.agent3_seconds}s</span></div>
        <div class='timing-pill'>Agent 4 <span>{pr.timing.agent4_seconds}s</span></div>
        <div class='timing-pill'>Papers <span>{len(pr.papers)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # ── advanced / transparency panel ───────────────────────────
    with st.expander("🔎 Pipeline Transparency — PICO, MeSH Terms & Query", expanded=False):

        tab1, tab2, tab3, tab4 = st.tabs(["🧠 PICO", "🏷️ MeSH Terms", "🔧 PubMed Query", "📈 Feedback"])

        with tab1:
            if pr.pico:
                comparison_val = pr.pico.comparison if pr.pico.comparison else "Not specified"
                st.markdown(f"""
                <div class='pico-grid'>
                    <div class='pico-item pico-P'>
                        <div class='pico-label'>P — Population</div>
                        <div class='pico-value'>{pr.pico.population or "—"}</div>
                    </div>
                    <div class='pico-item pico-I'>
                        <div class='pico-label'>I — Intervention</div>
                        <div class='pico-value'>{pr.pico.intervention or "—"}</div>
                    </div>
                    <div class='pico-item pico-C'>
                        <div class='pico-label'>C — Comparison</div>
                        <div class='pico-value'>{comparison_val}</div>
                    </div>
                    <div class='pico-item pico-O'>
                        <div class='pico-label'>O — Outcome</div>
                        <div class='pico-value'>{pr.pico.outcome or "—"}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with tab2:
            if pr.mesh_mappings:
                all_mesh = []
                for term, mappings in pr.mesh_mappings.mesh_mappings.items():
                    st.markdown(f"**`{term}`** →")
                    tags_html = "".join([f"<span class='mesh-tag'>{m}</span>" for m in mappings])
                    st.markdown(f"<div class='mesh-container'>{tags_html}</div>", unsafe_allow_html=True)
                    all_mesh.extend(mappings)
                    st.markdown("---")

        with tab3:
            if pr.pubmed_query:
                st.markdown(f"""
                <div class='query-box'>{pr.pubmed_query.query_string}</div>
                """, unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Complexity", pr.pubmed_query.estimated_complexity.upper())
                with col_b:
                    st.metric("Field Tags", ", ".join(pr.pubmed_query.field_tags))
                with col_c:
                    st.metric("Papers Found", len(pr.papers))
                if st.button("📋 Copy Query to Clipboard", key="copy_query"):
                    st.code(pr.pubmed_query.query_string)
                    st.caption("Select all and copy from the box above")

        with tab4:
            if pr.feedback_suggestions:
                st.success("✅ Feedback learner has suggestions for this topic")
                for k, v in pr.feedback_suggestions.items():
                    st.markdown(f"**{k.replace('_', ' ').title()}:** `{v}`")
            else:
                st.info("🌱 Cold start — no past interactions yet. Mark papers as relevant/not relevant to train the system.")
                st.caption("The feedback learner activates after 10+ interactions on similar topics.")

    # ── results header ──────────────────────────────────────────
    rel_count = sum(1 for v in st.session_state.interactions.values() if v == "relevant")
    irrel_count = sum(1 for v in st.session_state.interactions.values() if v == "irrelevant")

    st.markdown(f"""
    <div class='section-label'>
        📄 {len(pr.papers)} Papers — ranked by relevance
        {'&nbsp;&nbsp;✓ ' + str(rel_count) + ' relevant' if rel_count else ''}
        {'&nbsp;&nbsp;✗ ' + str(irrel_count) + ' not relevant' if irrel_count else ''}
    </div>
    """, unsafe_allow_html=True)

    # ── paper cards ─────────────────────────────────────────────
    if not pr.papers:
        st.warning("No papers returned. Try a broader question or check your PubMed query in the transparency panel.")
    else:
        for i, paper in enumerate(pr.papers):
            interaction = st.session_state.interactions.get(paper.pmid, None)
            card_class = "paper-card relevant" if interaction == "relevant" else \
                         "paper-card irrelevant" if interaction == "irrelevant" else "paper-card"

            score_pct = int(paper.relevance_score * 100)
            score_color = "#48bb78" if score_pct >= 75 else "#63b3ed" if score_pct >= 50 else "#f6ad55"

            # highlights
            highlights_html = ""
            if paper.highlighted_sentences:
                for sent in paper.highlighted_sentences:
                    if sent.strip():
                        highlights_html += f"<div class='highlight-box'>💡 {sent}</div>"
            else:
                highlights_html = "<div class='no-highlight'>No highlighted sentences extracted</div>"

            st.markdown(f"""
            <div class='{card_class}'>
                <div class='paper-rank'>#{i+1} &nbsp;|&nbsp; {score_pct}% match</div>
                <div class='paper-title'>{paper.title}</div>
                <div class='paper-meta'>
                    <span>📅 {paper.year if paper.year else 'Year unknown'}</span>
                    <span>🔑 PMID: {paper.pmid}</span>
                </div>
                {highlights_html}
                <div class='score-row'>
                    <div class='score-label'>Relevance</div>
                    <div class='score-bar-bg'><div class='score-bar-fill' style='width:{score_pct}%; background: linear-gradient(90deg, #63b3ed, {score_color});'></div></div>
                    <div class='score-value'>{paper.relevance_score:.3f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # buttons row
            btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 4])

            with btn_col1:
                rel_label = "✓ Relevant" if interaction != "relevant" else "✓ Marked"
                if st.button(rel_label, key=f"rel_{paper.pmid}_{i}",
                             use_container_width=True,
                             type="primary" if interaction == "relevant" else "secondary"):
                    st.session_state.interactions[paper.pmid] = "relevant"
                    record_user_interaction(
                        session_id=st.session_state.session_id,
                        pmid=paper.pmid,
                        action="clicked",
                        query_string=pr.pubmed_query.query_string if pr.pubmed_query else "",
                        mesh_terms=list(pr.mesh_mappings.mesh_mappings.values())[0] if pr.mesh_mappings else []
                    )
                    st.rerun()

            with btn_col2:
                irrel_label = "✗ Not Relevant" if interaction != "irrelevant" else "✗ Marked"
                if st.button(irrel_label, key=f"irrel_{paper.pmid}_{i}",
                             use_container_width=True):
                    st.session_state.interactions[paper.pmid] = "irrelevant"
                    record_user_interaction(
                        session_id=st.session_state.session_id,
                        pmid=paper.pmid,
                        action="skipped",
                        query_string=pr.pubmed_query.query_string if pr.pubmed_query else "",
                        mesh_terms=list(pr.mesh_mappings.mesh_mappings.values())[0] if pr.mesh_mappings else []
                    )
                    st.rerun()

            with btn_col3:
                st.link_button("🔗 PubMed", paper.pubmed_url, use_container_width=True)

            st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)