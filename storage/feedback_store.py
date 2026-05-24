import sqlite3
from pathlib import Path
from datetime import datetime
from datetime import datetime, timezone

DB_PATH = Path("storage/feedback.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            pmid TEXT NOT NULL,
            action TEXT NOT NULL,
            query_string TEXT,
            mesh_terms TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_string TEXT NOT NULL,
            mesh_terms_used TEXT,
            result_count INTEGER,
            click_through_rate REAL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("[FeedbackStore] Database initialized")


def record_interaction(
    session_id: str,
    pmid: str,
    action: str,
    query_string: str = "",
    mesh_terms: list[str] = None
):
    valid_actions = ["clicked", "skipped", "rated_relevant", "rated_irrelevant"]
    if action not in valid_actions:
        raise ValueError(f"Action must be one of {valid_actions}, got: {action}")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO interactions
        (session_id, pmid, action, query_string, mesh_terms, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        pmid,
        action,
        query_string,
        ",".join(mesh_terms) if mesh_terms else "",
        datetime.now(timezone.utc).isoformat()
    ))

    conn.commit()
    conn.close()
    print(f"[FeedbackStore] Recorded: session={session_id} pmid={pmid} action={action}")


def get_click_through_rate(query_pattern: str) -> float:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action FROM interactions
        WHERE query_string LIKE ?
    """, (f"%{query_pattern}%",))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return 0.0

    total = len(rows)
    clicks = sum(1 for r in rows if r["action"] in ["clicked", "rated_relevant"])
    ctr = round(clicks / total, 4)
    print(f"[FeedbackStore] CTR for '{query_pattern}': {clicks}/{total} = {ctr}")
    return ctr


def get_top_mesh_terms(topic: str, limit: int = 5) -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT mesh_terms FROM interactions
        WHERE action IN ('clicked', 'rated_relevant')
        AND (query_string LIKE ? OR mesh_terms LIKE ?)
    """, (f"%{topic}%", f"%{topic}%"))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    term_counts = {}
    for row in rows:
        if row["mesh_terms"]:
            for term in row["mesh_terms"].split(","):
                term = term.strip()
                if term:
                    term_counts[term] = term_counts.get(term, 0) + 1

    sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
    top = [term for term, count in sorted_terms[:limit]]
    print(f"[FeedbackStore] Top MeSH terms for '{topic}': {top}")
    return top


def get_query_suggestions(topic: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as total FROM interactions
        WHERE query_string LIKE ?
    """, (f"%{topic}%",))

    total_row = cursor.fetchone()
    total_interactions = total_row["total"] if total_row else 0

    if total_interactions < 10:
        conn.close()
        print(f"[FeedbackStore] Not enough data for '{topic}' ({total_interactions}/10 interactions)")
        return {}

    cursor.execute("""
        SELECT mesh_terms, action FROM interactions
        WHERE query_string LIKE ?
    """, (f"%{topic}%",))

    rows = cursor.fetchall()
    conn.close()

    clicked_terms = {}
    skipped_terms = {}

    for row in rows:
        if not row["mesh_terms"]:
            continue
        terms = [t.strip() for t in row["mesh_terms"].split(",") if t.strip()]
        for term in terms:
            if row["action"] in ["clicked", "rated_relevant"]:
                clicked_terms[term] = clicked_terms.get(term, 0) + 1
            elif row["action"] in ["skipped", "rated_irrelevant"]:
                skipped_terms[term] = skipped_terms.get(term, 0) + 1

    suggestions = {}

    if clicked_terms:
        best_term = max(clicked_terms.items(), key=lambda x: x[1])
        suggestions["prefer_terms"] = [best_term[0]]

    if skipped_terms:
        worst_term = max(skipped_terms.items(), key=lambda x: x[1])
        suggestions["avoid_terms"] = [worst_term[0]]

    rct_clicks = sum(1 for r in rows if r["action"] == "clicked")
    if rct_clicks > 5:
        suggestions["add_filter"] = "Randomized Controlled Trial"

    print(f"[FeedbackStore] Suggestions for '{topic}': {suggestions}")
    return suggestions