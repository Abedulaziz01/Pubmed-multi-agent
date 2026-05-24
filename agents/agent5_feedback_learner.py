from storage.feedback_store import (
    init_db,
    record_interaction,
    get_click_through_rate,
    get_top_mesh_terms,
    get_query_suggestions
)

# initialize database on import
init_db()


def record_user_interaction(
    session_id: str,
    pmid: str,
    action: str,
    query_string: str = "",
    mesh_terms: list[str] = None
):
    record_interaction(
        session_id=session_id,
        pmid=pmid,
        action=action,
        query_string=query_string,
        mesh_terms=mesh_terms or []
    )


def get_historical_ctr(query_pattern: str) -> float:
    return get_click_through_rate(query_pattern)


def get_top_performing_mesh_terms(topic: str) -> list[str]:
    return get_top_mesh_terms(topic)


def suggest_query_improvements(query: str) -> dict:
    topic = _extract_topic(query)
    suggestions = get_query_suggestions(topic)

    if not suggestions:
        print(f"[Agent 5] No suggestions yet for topic: '{topic}' — need 10+ interactions")
        return {}

    print(f"[Agent 5] Suggestions for '{topic}': {suggestions}")
    return suggestions


def format_suggestions_for_prompt(suggestions: dict) -> str:
    if not suggestions:
        return ""

    lines = ["Based on past user interactions, apply these improvements:"]

    if "prefer_terms" in suggestions:
        lines.append(f"- PREFER these MeSH terms: {', '.join(suggestions['prefer_terms'])}")

    if "avoid_terms" in suggestions:
        lines.append(f"- AVOID these MeSH terms (users skipped them): {', '.join(suggestions['avoid_terms'])}")

    if "add_filter" in suggestions:
        lines.append(f"- ADD this publication filter: {suggestions['add_filter']}")

    return "\n".join(lines)


def _extract_topic(query: str) -> str:
    stop_words = {"does", "do", "is", "are", "can", "will", "the", "a", "an",
                  "help", "helps", "reduce", "reduces", "for", "in", "with",
                  "and", "or", "to", "of", "on"}
    words = query.lower().replace("?", "").split()
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    return " ".join(keywords[:3]) if keywords else query[:30]