import streamlit as st
import streamlit.components.v1 as components
import uuid
import time
import sys
import csv
import io
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pipeline import run_pipeline
from agents.agent5_feedback_learner import record_user_interaction
from storage.feedback_store import init_db

init_db()

st.set_page_config(
    page_title="PubMed AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
* { margin:0; padding:0; box-sizing:border-box; font-family:'Inter',sans-serif; }
body { background:transparent; }
.paper-card {
    background:#1a1f2e; border:1px solid #2d3561; border-radius:14px;
    padding:20px 22px; margin-bottom:14px; position:relative;
}
.paper-card.relevant { border-color:#48bb78; border-left:4px solid #48bb78; }
.paper-card.irrelevant { border-color:#fc8181; border-left:4px solid #fc8181; }
.paper-card.bookmarked { border-color:#f6ad55; border-left:4px solid #f6ad55; }
.paper-rank {
    position:absolute; top:14px; right:14px;
    background:rgba(99,179,237,0.1); border:1px solid rgba(99,179,237,0.2);
    border-radius:8px; padding:3px 9px; font-size:0.68rem; color:#63b3ed;
    font-family:'JetBrains Mono',monospace; font-weight:500;
}
.paper-title { font-size:0.97rem; font-weight:600; color:#e2e8f0; margin:0 0 5px 0; padding-right:80px; line-height:1.4; }
.paper-meta { font-size:0.76rem; color:#8892a4; margin-bottom:12px; display:flex; gap:14px; flex-wrap:wrap; }
.highlight-box {
    background:rgba(246,173,85,0.08); border-left:3px solid #f6ad55;
    border-radius:0 8px 8px 0; padding:9px 13px; margin-bottom:7px;
    font-size:0.83rem; color:#e2e8f0; line-height:1.6; font-style:italic;
}
.no-highlight { font-size:0.8rem; color:#4a5568; font-style:italic; margin-bottom:8px; }
.score-row { display:flex; align-items:center; gap:10px; margin-top:12px; }
.score-label { font-size:0.66rem; color:#8892a4; white-space:nowrap; font-weight:500; }
.score-bar-bg { flex:1; height:5px; background:#2d3561; border-radius:3px; overflow:hidden; }
.score-bar-fill { height:100%; border-radius:3px; }
.score-value { font-size:0.68rem; color:#63b3ed; font-family:'JetBrains Mono',monospace; font-weight:500; min-width:34px; text-align:right; }
.badge-gold { color:#d29922; }
.badge-green { color:#3fb950; }
.badge-red { color:#f85149; }
</style>
"""

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }
.topbar { display:flex; align-items:center; justify-content:space-between; padding:10px 20px; background:#161b22; border:1px solid #21262d; border-radius:12px; margin-bottom:16px; flex-wrap:wrap; gap:10px; }
.topbar-brand { display:flex; align-items:center; gap:10px; }
.topbar-logo { font-size:1.6rem; line-height:1; }
.topbar-title { font-size:0.95rem; font-weight:700; color:#e6edf3; }
.topbar-sub { font-size:0.6rem; color:#6e7681; text-transform:uppercase; letter-spacing:0.08em; }
.topbar-stats { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
.stat-chip { background:#21262d; border:1px solid #30363d; border-radius:8px; padding:4px 10px; font-size:0.7rem; color:#8b949e; font-family:'JetBrains Mono',monospace; display:flex; align-items:center; gap:4px; }
.stat-chip b { color:#58a6ff; font-weight:600; }
.stat-chip.green b { color:#3fb950; }
.stat-chip.red b { color:#f85149; }
.stat-chip.gold b { color:#d29922; }
.prog-wrap { background:#21262d; border-radius:4px; height:5px; overflow:hidden; width:60px; display:inline-block; vertical-align:middle; margin:0 4px; }
.prog-fill { height:100%; border-radius:4px; background:linear-gradient(90deg,#388bfd,#bc8cff); }
.hero-container { background:linear-gradient(135deg,#1a1f2e 0%,#16213e 50%,#0f3460 100%); border:1px solid #2d3561; border-radius:16px; padding:36px 40px; margin-bottom:22px; text-align:center; }
.hero-title { font-size:2.2rem; font-weight:700; background:linear-gradient(135deg,#63b3ed,#9f7aea,#63b3ed); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin:0 0 8px 0; }
.hero-subtitle { color:#8892a4; font-size:1rem; margin:0; }
.hero-badges { margin-top:14px; display:flex; gap:8px; justify-content:center; flex-wrap:wrap; }
.badge { background:rgba(99,179,237,0.1); border:1px solid rgba(99,179,237,0.3); color:#63b3ed; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:500; }
.pipeline-container { background:#1a1f2e; border:1px solid #2d3561; border-radius:12px; padding:18px 22px; margin-bottom:18px; }
.pipeline-title { color:#8892a4; font-size:0.68rem; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:14px; }
.steps-row { display:flex; align-items:center; }
.step-item { display:flex; flex-direction:column; align-items:center; flex:1; }
.step-circle { width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.95rem; font-weight:600; border:2px solid #2d3561; background:#0f1117; color:#4a5568; z-index:2; }
.step-circle.active { border-color:#63b3ed; background:rgba(99,179,237,0.15); color:#63b3ed; box-shadow:0 0 14px rgba(99,179,237,0.3); }
.step-circle.done { border-color:#48bb78; background:rgba(72,187,120,0.15); color:#48bb78; }
.step-circle.error { border-color:#fc8181; background:rgba(252,129,129,0.15); color:#fc8181; }
.step-label { font-size:0.62rem; color:#4a5568; margin-top:5px; text-align:center; font-weight:500; white-space:nowrap; }
.step-label.active { color:#63b3ed; }
.step-label.done { color:#48bb78; }
.step-connector { flex:1; height:2px; background:#2d3561; margin-top:-18px; z-index:1; }
.step-connector.done { background:#48bb78; }
.timing-row { display:flex; gap:6px; flex-wrap:wrap; margin-top:10px; }
.timing-pill { background:rgba(99,179,237,0.08); border:1px solid rgba(99,179,237,0.2); border-radius:20px; padding:3px 10px; font-size:0.68rem; color:#8892a4; font-family:'JetBrains Mono',monospace; }
.timing-pill span { color:#63b3ed; font-weight:500; }
.pico-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-top:10px; }
.pico-item { background:#0f1117; border:1px solid #2d3561; border-radius:10px; padding:12px 14px; }
.pico-label { font-size:0.62rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:5px; }
.pico-value { font-size:0.88rem; color:#e2e8f0; font-weight:400; }
.pico-P .pico-label { color:#63b3ed; }
.pico-I .pico-label { color:#9f7aea; }
.pico-C .pico-label { color:#f6ad55; }
.pico-O .pico-label { color:#68d391; }
.query-box { background:#0f1117; border:1px solid #2d3561; border-radius:10px; padding:12px 14px; margin-top:10px; font-family:'JetBrains Mono',monospace; font-size:0.76rem; color:#63b3ed; line-height:1.6; word-break:break-all; }
.mesh-container { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
.mesh-tag { background:rgba(159,122,234,0.1); border:1px solid rgba(159,122,234,0.3); color:#9f7aea; padding:2px 9px; border-radius:6px; font-size:0.7rem; font-weight:500; }
.section-label { font-size:0.68rem; font-weight:700; color:#8892a4; letter-spacing:0.1em; text-transform:uppercase; margin:20px 0 10px 0; display:flex; align-items:center; gap:8px; }
.section-label::after { content:''; flex:1; height:1px; background:#2d3561; }
.empty-state { text-align:center; padding:60px 20px; }
.empty-icon { font-size:3rem; margin-bottom:16px; }
.empty-title { font-size:1.1rem; color:#8892a4; margin-bottom:8px; font-weight:500; }
.empty-subtitle { font-size:0.85rem; color:#4a5568; }
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)


# ── session state ─────────────────────────────────────────────────
defaults = {
    "session_id": str(uuid.uuid4())[:8],
    "pipeline_result": None,
    "query_history": [],
    "interactions": {},
    "bookmarks": {},
    "current_query": "",
    "filter_year_min": 2000,
    "filter_year_max": 2025,
    "filter_min_score": 0.0,
    "filter_study_type": "All",
    "all_search_stats": [],
    "show_history": False,
    "show_bookmarks": False,
    "show_filters": False,
    "show_export": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── helpers ───────────────────────────────────────────────────────
def export_csv(papers):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Rank","Title","Year","PMID","Score","Highlights","URL"])
    for i, p in enumerate(papers):
        w.writerow([i+1, p.title, p.year, p.pmid, round(p.relevance_score,4),
                    " | ".join(p.highlighted_sentences), p.pubmed_url])
    return buf.getvalue()

def export_json(papers, pico, query):
    return json.dumps({
        "question": st.session_state.current_query,
        "pico": pico.dict() if pico else {},
        "pubmed_query": query.query_string if query else "",
        "papers": [{"rank":i+1,"title":p.title,"year":p.year,"pmid":p.pmid,
                    "score":round(p.relevance_score,4),
                    "highlights":p.highlighted_sentences,"url":p.pubmed_url}
                   for i,p in enumerate(papers)]
    }, indent=2)

def export_summary(papers, question):
    lines = ["Literature Summary", f"Question: {question}", "="*60, ""]
    for i, p in enumerate(papers):
        lines.append(f"{i+1}. {p.title} ({p.year})")
        lines.append(f"   PMID: {p.pmid} | Score: {round(p.relevance_score,3)}")
        for s in p.highlighted_sentences:
            lines.append(f"   → {s}")
        lines.append("")
    return "\n".join(lines)

def render_pipeline_tracker(steps):
    defs = [("1","PICO","agent1"),("2","MeSH","agent2"),
            ("3","Query","agent3"),("4","Search","agent4"),("5","Rank","agent5_rank")]
    html = ""
    for i, (num, label, key) in enumerate(defs):
        state = steps.get(key, "pending")
        icon = {"done":"✓","active":"⟳","error":"✗","pending":num}[state]
        html += f"<div class='step-item'><div class='step-circle {state}'>{icon}</div><div class='step-label {state}'>{label}</div></div>"
        if i < len(defs)-1:
            cc = "done" if steps.get(key)=="done" else ""
            html += f"<div class='step-connector {cc}'></div>"
    st.markdown(
        f"<div class='pipeline-container'><div class='pipeline-title'>⚡ Pipeline Progress</div><div class='steps-row'>{html}</div></div>",
        unsafe_allow_html=True
    )

def render_card(paper, i, interaction, is_bm):
    if is_bm: cc = "paper-card bookmarked"
    elif interaction == "relevant": cc = "paper-card relevant"
    elif interaction == "irrelevant": cc = "paper-card irrelevant"
    else: cc = "paper-card"

    score_pct = int(paper.relevance_score * 100)
    sc = "#3fb950" if score_pct >= 75 else "#58a6ff" if score_pct >= 50 else "#d29922"

    hl = ""
    if paper.highlighted_sentences:
        for s in paper.highlighted_sentences:
            if s.strip():
                hl += "<div class='highlight-box'>💡 " + s.replace("'", "&#39;").replace('"', "&quot;") + "</div>"
    else:
        hl = "<div class='no-highlight'>No highlighted sentences extracted</div>"

    bm_badge = "<span class='badge-gold'>🔖 Saved</span>" if is_bm else ""
    rel_badge = "<span class='badge-green'>✓ Relevant</span>" if interaction == "relevant" else ""
    irrel_badge = "<span class='badge-red'>✗ Not Relevant</span>" if interaction == "irrelevant" else ""

    title_safe = paper.title.replace("'", "&#39;").replace('"', "&quot;")

    html = (
        CARD_CSS +
        "<div class='" + cc + "'>"
        "<div class='paper-rank'>#" + str(i+1) + " &nbsp;·&nbsp; " + str(score_pct) + "%</div>"
        "<div class='paper-title'>" + title_safe + "</div>"
        "<div class='paper-meta'>"
        "<span>📅 " + str(paper.year or "Unknown") + "</span>"
        " <span>🔑 " + paper.pmid + "</span>"
        " " + bm_badge + " " + rel_badge + " " + irrel_badge +
        "</div>"
        + hl +
        "<div class='score-row'>"
        "<div class='score-label'>Relevance</div>"
        "<div class='score-bar-bg'>"
        "<div class='score-bar-fill' style='width:" + str(score_pct) + "%;background:linear-gradient(90deg,#58a6ff," + sc + ");'></div>"
        "</div>"
        "<div class='score-value'>" + f"{paper.relevance_score:.3f}" + "</div>"
        "</div>"
        "</div>"
    )
    return html


# ══════════════════════════════════════════════════════════════════
# TOP NAV BAR
# ══════════════════════════════════════════════════════════════════
pr_now = st.session_state.pipeline_result
total_papers = len(pr_now.papers) if pr_now and pr_now.success else 0
rel_count = sum(1 for v in st.session_state.interactions.values() if v == "relevant")
irrel_count = sum(1 for v in st.session_state.interactions.values() if v == "irrelevant")
bookmark_count = len(st.session_state.bookmarks)
total_int = rel_count + irrel_count
pct = min(100, int(total_int/10*100))

st.markdown(f"""
<div class="topbar">
    <div class="topbar-brand">
        <div class="topbar-logo">🔬</div>
        <div>
            <div class="topbar-title">PubMed AI</div>
            <div class="topbar-sub">Research Assistant</div>
        </div>
    </div>
    <div class="topbar-stats">
        <div class="stat-chip">Session <b>#{st.session_state.session_id}</b></div>
        <div class="stat-chip">Searches <b>{len(st.session_state.query_history)}</b></div>
        <div class="stat-chip">Papers <b>{total_papers}</b></div>
        <div class="stat-chip green">✓ <b>{rel_count}</b></div>
        <div class="stat-chip red">✗ <b>{irrel_count}</b></div>
        <div class="stat-chip gold">🔖 <b>{bookmark_count}</b></div>
        <div class="stat-chip">AI Learning <div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div><b>{total_int}/10</b></div>
    </div>
</div>
""", unsafe_allow_html=True)

# nav buttons
nb1, nb2, nb3, nb4, nb5 = st.columns([1,1,1,1,4])
with nb1:
    if st.button(f"🕐 History ({len(st.session_state.query_history)})", use_container_width=True, key="tog_hist"):
        st.session_state.show_history = not st.session_state.show_history
        st.session_state.show_bookmarks = False
        st.session_state.show_filters = False
        st.session_state.show_export = False
with nb2:
    if st.button(f"🔖 Saved ({bookmark_count})", use_container_width=True, key="tog_bm"):
        st.session_state.show_bookmarks = not st.session_state.show_bookmarks
        st.session_state.show_history = False
        st.session_state.show_filters = False
        st.session_state.show_export = False
with nb3:
    if st.button("🎛️ Filters", use_container_width=True, key="tog_filt"):
        st.session_state.show_filters = not st.session_state.show_filters
        st.session_state.show_history = False
        st.session_state.show_bookmarks = False
        st.session_state.show_export = False
with nb4:
    if st.button("📥 Export", use_container_width=True, key="tog_exp"):
        st.session_state.show_export = not st.session_state.show_export
        st.session_state.show_history = False
        st.session_state.show_bookmarks = False
        st.session_state.show_filters = False

# ── History panel ─────────────────────────────────────────────────
if st.session_state.show_history:
    with st.container(border=True):
        st.markdown("**🕐 Search History**")
        if not st.session_state.query_history:
            st.caption("No searches yet")
        else:
            cols = st.columns(4)
            for i, q in enumerate(reversed(st.session_state.query_history[-8:])):
                num = len(st.session_state.query_history) - i
                with cols[i % 4]:
                    if st.button(f"#{num} {q[:30]}...", key=f"hbtn_{i}", use_container_width=True):
                        st.session_state["_rerun_query"] = q
                        st.session_state.show_history = False
                        st.rerun()

# ── Bookmarks panel ───────────────────────────────────────────────
if st.session_state.show_bookmarks:
    with st.container(border=True):
        st.markdown("**🔖 Saved Papers**")
        if not st.session_state.bookmarks:
            st.caption("No bookmarks yet. Click 🔖 on any paper.")
        else:
            cols = st.columns(4)
            for idx, (pmid, info) in enumerate(list(st.session_state.bookmarks.items())):
                with cols[idx % 4]:
                    st.markdown(f"**{info['title'][:45]}...**")
                    st.caption(f"PMID {pmid} · {info.get('year','?')} · score {info.get('score','?')}")
                    if st.button("Remove", key=f"rmbm_{pmid}", use_container_width=True):
                        del st.session_state.bookmarks[pmid]
                        st.rerun()
            if st.button("🗑️ Clear all bookmarks", key="clr_all"):
                st.session_state.bookmarks = {}
                st.rerun()

# ── Filters panel ─────────────────────────────────────────────────
if st.session_state.show_filters:
    with st.container(border=True):
        st.markdown("**🎛️ Search Filters**")
        fc1, fc2, fc3, fc4 = st.columns([2,2,2,1])
        with fc1:
            year_min, year_max = st.slider("Year range", 1990, 2025,
                (st.session_state.filter_year_min, st.session_state.filter_year_max), key="year_slider")
            st.session_state.filter_year_min = year_min
            st.session_state.filter_year_max = year_max
        with fc2:
            min_score = st.slider("Min relevance score", 0.0, 1.0,
                st.session_state.filter_min_score, step=0.05, key="score_slider")
            st.session_state.filter_min_score = min_score
        with fc3:
            study_opts = ["All","Randomized Controlled Trial","Review","Meta-Analysis","Clinical Trial","Observational Study"]
            study_type = st.selectbox("Study type", study_opts,
                index=study_opts.index(st.session_state.filter_study_type), key="study_select")
            st.session_state.filter_study_type = study_type
        with fc4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("↺ Reset", key="reset_filters", use_container_width=True):
                st.session_state.filter_year_min = 2000
                st.session_state.filter_year_max = 2025
                st.session_state.filter_min_score = 0.0
                st.session_state.filter_study_type = "All"
                st.rerun()

# ── Export panel ──────────────────────────────────────────────────
if st.session_state.show_export:
    with st.container(border=True):
        st.markdown("**📥 Export Results**")
        if not pr_now or not pr_now.success or not pr_now.papers:
            st.info("Run a search first to enable export.")
        else:
            ec1, ec2, ec3, ec4 = st.columns(4)
            with ec1:
                st.download_button("📄 CSV", export_csv(pr_now.papers),
                    file_name=f"pubmed_{st.session_state.session_id}.csv",
                    mime="text/csv", use_container_width=True, key="dl_csv")
            with ec2:
                st.download_button("📦 JSON", export_json(pr_now.papers, pr_now.pico, pr_now.pubmed_query),
                    file_name=f"pubmed_{st.session_state.session_id}.json",
                    mime="application/json", use_container_width=True, key="dl_json")
            with ec3:
                st.download_button("📝 Summary", export_summary(pr_now.papers, st.session_state.current_query),
                    file_name=f"summary_{st.session_state.session_id}.txt",
                    mime="text/plain", use_container_width=True, key="dl_txt")
            with ec4:
                hl = []
                for p in pr_now.papers:
                    if p.highlighted_sentences:
                        hl.append(f"[{p.title[:50]}]")
                        hl += [f"  • {s}" for s in p.highlighted_sentences]
                        hl.append("")
                if hl:
                    st.download_button("💡 Highlights", "\n".join(hl),
                        file_name=f"highlights_{st.session_state.session_id}.txt",
                        mime="text/plain", use_container_width=True, key="dl_hl")


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

if "_rerun_query" in st.session_state:
    rq = st.session_state.pop("_rerun_query")
    st.session_state.current_query = rq
    if rq not in st.session_state.query_history:
        st.session_state.query_history.append(rq)
    with st.spinner(f"Re-running: {rq}"):
        r = run_pipeline(rq)
        st.session_state.pipeline_result = r
        st.session_state.interactions = {}

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

c1, c2 = st.columns([5, 1])
with c1:
    query = st.text_input("q", placeholder="e.g. Does exercise help depressed teenagers?",
                          label_visibility="collapsed", key="query_input",
                          value=st.session_state.current_query if st.session_state.current_query else "")
with c2:
    search_clicked = st.button("🔍 Search", use_container_width=True, type="primary")

ex_cols = st.columns(4)
examples = ["Does exercise help depressed teenagers?","Is aspirin effective for headaches?",
            "Does walking reduce back pain?","Can meditation reduce anxiety?"]
for i, (col, ex) in enumerate(zip(ex_cols, examples)):
    with col:
        if st.button(ex[:26]+"...", key=f"ex_{i}", use_container_width=True):
            query = ex
            search_clicked = True

active_filters = []
if st.session_state.filter_year_min != 2000 or st.session_state.filter_year_max != 2025:
    active_filters.append(f"📅 {st.session_state.filter_year_min}–{st.session_state.filter_year_max}")
if st.session_state.filter_min_score > 0:
    active_filters.append(f"⭐ ≥{st.session_state.filter_min_score}")
if st.session_state.filter_study_type != "All":
    active_filters.append(f"📋 {st.session_state.filter_study_type}")
if active_filters:
    pills = " ".join([f"<span style='background:rgba(88,166,255,0.1);border:1px solid rgba(88,166,255,0.3);color:#58a6ff;padding:2px 10px;border-radius:12px;font-size:0.7rem;'>{f}</span>" for f in active_filters])
    st.markdown(f"<div style='margin:6px 0 2px;display:flex;gap:6px;flex-wrap:wrap;align-items:center;'><span style='font-size:0.66rem;color:#6e7681;'>Active:</span>{pills}</div>", unsafe_allow_html=True)

if search_clicked and query.strip():
    st.session_state.current_query = query.strip()
    if query.strip() not in st.session_state.query_history:
        st.session_state.query_history.append(query.strip())
    steps = {}
    pp = st.empty()
    sp = st.empty()
    with st.spinner(""):
        with pp.container(): render_pipeline_tracker(steps)
        steps["agent1"] = "active"
        sp.info("🧠 Agent 1 — Extracting PICO...")
        with pp.container(): render_pipeline_tracker(steps)
        try:
            result = run_pipeline(query.strip())
            if result.success:
                steps = {k:"done" for k in ["agent1","agent2","agent3","agent4","agent5_rank"]}
            else:
                failed = result.failed_at_agent or ""
                keys = ["agent1","agent2","agent3","agent4","agent5_rank"]
                for j, k in enumerate(keys):
                    if str(j+1) in failed:
                        steps = {ak:"done" for ak in keys[:j]}
                        steps[k] = "error"
                        break
            with pp.container(): render_pipeline_tracker(steps)
            st.session_state.pipeline_result = result
            st.session_state.interactions = {}
            sp.empty()
            if result.success:
                st.session_state.all_search_stats.append({
                    "query": query.strip(), "papers": len(result.papers),
                    "time": result.timing.total_seconds,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
        except Exception as e:
            steps["agent1"] = "error"
            with pp.container(): render_pipeline_tracker(steps)
            sp.error(f"Pipeline error: {e}")
            st.stop()

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
    st.error(f"Pipeline failed at {pr.failed_at_agent}")
    st.code(pr.error_message)

else:
    st.markdown(f"""
    <div class='timing-row'>
        <div class='timing-pill'>Total <span>{pr.timing.total_seconds}s</span></div>
        <div class='timing-pill'>A1 <span>{pr.timing.agent1_seconds}s</span></div>
        <div class='timing-pill'>A2 <span>{pr.timing.agent2_seconds}s</span></div>
        <div class='timing-pill'>A3 <span>{pr.timing.agent3_seconds}s</span></div>
        <div class='timing-pill'>A4 <span>{pr.timing.agent4_seconds}s</span></div>
        <div class='timing-pill'>Papers <span>{len(pr.papers)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔎 Pipeline Transparency — PICO · MeSH · Query · Feedback", expanded=False):
        t1, t2, t3, t4 = st.tabs(["🧠 PICO","🏷️ MeSH","🔧 Query","📈 Feedback"])
        with t1:
            if pr.pico:
                st.markdown(f"""
                <div class='pico-grid'>
                    <div class='pico-item pico-P'><div class='pico-label'>P — Population</div><div class='pico-value'>{pr.pico.population or "—"}</div></div>
                    <div class='pico-item pico-I'><div class='pico-label'>I — Intervention</div><div class='pico-value'>{pr.pico.intervention or "—"}</div></div>
                    <div class='pico-item pico-C'><div class='pico-label'>C — Comparison</div><div class='pico-value'>{pr.pico.comparison or "Not specified"}</div></div>
                    <div class='pico-item pico-O'><div class='pico-label'>O — Outcome</div><div class='pico-value'>{pr.pico.outcome or "—"}</div></div>
                </div>
                """, unsafe_allow_html=True)
        with t2:
            if pr.mesh_mappings:
                for term, mappings in pr.mesh_mappings.mesh_mappings.items():
                    st.markdown(f"**`{term}`** →")
                    tags = "".join([f'<span class="mesh-tag">{m}</span>' for m in mappings])
                    st.markdown(f"<div class='mesh-container'>{tags}</div>", unsafe_allow_html=True)
                    st.markdown("---")
        with t3:
            if pr.pubmed_query:
                st.markdown(f"<div class='query-box'>{pr.pubmed_query.query_string}</div>", unsafe_allow_html=True)
                ca, cb, cc = st.columns(3)
                with ca: st.metric("Complexity", pr.pubmed_query.estimated_complexity.upper())
                with cb: st.metric("Tags", ", ".join(pr.pubmed_query.field_tags))
                with cc: st.metric("Papers", len(pr.papers))
        with t4:
            if pr.feedback_suggestions:
                st.success("✅ Feedback learner active")
                for k, v in pr.feedback_suggestions.items():
                    st.markdown(f"**{k.replace('_',' ').title()}:** `{v}`")
            else:
                st.info("🌱 Mark papers relevant/not relevant to train the system")

    filtered_papers = pr.papers
    if st.session_state.filter_min_score > 0:
        filtered_papers = [p for p in filtered_papers if p.relevance_score >= st.session_state.filter_min_score]
    if st.session_state.filter_year_min != 2000 or st.session_state.filter_year_max != 2025:
        filtered_papers = [p for p in filtered_papers if st.session_state.filter_year_min <= (p.year or 0) <= st.session_state.filter_year_max]

    rel_count = sum(1 for v in st.session_state.interactions.values() if v == "relevant")
    irrel_count = sum(1 for v in st.session_state.interactions.values() if v == "irrelevant")

    label_parts = [f"📄 {len(filtered_papers)} papers"]
    if len(filtered_papers) < len(pr.papers):
        label_parts.append(f"(filtered from {len(pr.papers)})")
    else:
        label_parts.append("— ranked by relevance")
    if rel_count: label_parts.append(f"· ✓ {rel_count}")
    if irrel_count: label_parts.append(f"· ✗ {irrel_count}")

    st.markdown(
        "<div class='section-label'>" + " ".join(label_parts) + "</div>",
        unsafe_allow_html=True
    )

    if not filtered_papers:
        st.warning("No papers match your filters. Relax the year range or score threshold.")
    else:
        for i, paper in enumerate(filtered_papers):
            interaction = st.session_state.interactions.get(paper.pmid)
            is_bm = paper.pmid in st.session_state.bookmarks

            # render card using components.html — guaranteed to render HTML correctly
            card_html = render_card(paper, i, interaction, is_bm)
            components.html(card_html, height=280, scrolling=False)

            b1, b2, b3, b4, _ = st.columns([1, 1.2, 1, 1, 2])

            with b1:
                lbl = "✓ Marked" if interaction == "relevant" else "✓ Relevant"
                if st.button(lbl, key=f"rel_{paper.pmid}_{i}", use_container_width=True,
                             type="primary" if interaction == "relevant" else "secondary"):
                    st.session_state.interactions[paper.pmid] = "relevant"
                    record_user_interaction(
                        session_id=st.session_state.session_id, pmid=paper.pmid,
                        action="clicked",
                        query_string=pr.pubmed_query.query_string if pr.pubmed_query else "",
                        mesh_terms=list(pr.mesh_mappings.mesh_mappings.values())[0] if pr.mesh_mappings else []
                    )
                    st.rerun()

            with b2:
                lbl = "✗ Marked" if interaction == "irrelevant" else "✗ Not Relevant"
                if st.button(lbl, key=f"irrel_{paper.pmid}_{i}", use_container_width=True):
                    st.session_state.interactions[paper.pmid] = "irrelevant"
                    record_user_interaction(
                        session_id=st.session_state.session_id, pmid=paper.pmid,
                        action="skipped",
                        query_string=pr.pubmed_query.query_string if pr.pubmed_query else "",
                        mesh_terms=list(pr.mesh_mappings.mesh_mappings.values())[0] if pr.mesh_mappings else []
                    )
                    st.rerun()

            with b3:
                bm_lbl = "🔖 Saved" if is_bm else "🔖 Save"
                if st.button(bm_lbl, key=f"bm_{paper.pmid}_{i}", use_container_width=True):
                    if is_bm:
                        del st.session_state.bookmarks[paper.pmid]
                    else:
                        st.session_state.bookmarks[paper.pmid] = {
                            "title": paper.title, "year": paper.year,
                            "pmid": paper.pmid, "url": paper.pubmed_url,
                            "score": round(paper.relevance_score, 3)
                        }
                    st.rerun()

            with b4:
                st.link_button("🔗 PubMed", paper.pubmed_url, use_container_width=True)