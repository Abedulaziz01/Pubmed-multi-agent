import pytest
import os
from pathlib import Path
from storage.feedback_store import (
    init_db, record_interaction,
    get_click_through_rate, get_top_mesh_terms,
    get_query_suggestions
)
from agents.agent5_feedback_learner import (
    suggest_query_improvements,
    format_suggestions_for_prompt,
    record_user_interaction
)

DB_PATH = Path("storage/feedback.db")


def _reset_db():
    if DB_PATH.exists():
        os.remove(str(DB_PATH))
    init_db()


def test_database_initializes():
    _reset_db()
    assert DB_PATH.exists(), "feedback.db should be created after init_db()"
    print("\nDatabase file created successfully")


def test_record_interaction_writes_to_db():
    _reset_db()
    import sqlite3
    record_interaction("sess1", "pmid001", "clicked", "back pain walking", ["Walking", "Low Back Pain"])

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interactions")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 1
    print(f"\nRow written: {rows[0]}")


def test_invalid_action_raises_error():
    _reset_db()
    with pytest.raises(ValueError):
        record_interaction("sess1", "pmid001", "invalid_action")
    print("\nInvalid action correctly rejected")


def test_click_through_rate_5_clicks_5_skips():
    _reset_db()

    for i in range(5):
        record_interaction("sess1", f"pmid_c{i}", "clicked",
                         "back pain walking", ["Walking", "Low Back Pain"])
    for i in range(5):
        record_interaction("sess1", f"pmid_s{i}", "skipped",
                         "back pain walking", ["Walking"])

    ctr = get_click_through_rate("back pain")
    print(f"\nCTR: {ctr}")
    assert ctr == 0.5, f"Expected CTR of 0.5, got {ctr}"


def test_get_top_mesh_terms_after_clicks():
    _reset_db()

    for i in range(10):
        record_interaction("sess1", f"pmid{i}", "clicked",
                         "exercise aerobic", ["Aerobic Exercise", "Exercise"])

    top_terms = get_top_mesh_terms("exercise")
    print(f"\nTop MeSH terms: {top_terms}")

    assert len(top_terms) > 0
    assert "Aerobic Exercise" in top_terms, \
        f"Expected 'Aerobic Exercise' in top terms, got: {top_terms}"


def test_no_suggestions_under_10_interactions():
    _reset_db()

    for i in range(5):
        record_interaction("sess1", f"pmid{i}", "clicked",
                         "back pain", ["Low Back Pain"])

    suggestions = get_query_suggestions("back pain")
    print(f"\nSuggestions with 5 interactions: {suggestions}")
    assert suggestions == {}, \
        "Should return empty dict when fewer than 10 interactions"


def test_suggestions_appear_after_10_interactions():
    _reset_db()

    for i in range(8):
        record_interaction("sess1", f"pmid_c{i}", "clicked",
                         "back pain walking", ["Walking", "Low Back Pain"])
    for i in range(4):
        record_interaction("sess1", f"pmid_s{i}", "skipped",
                         "back pain walking", ["Mobility Limitation"])

    suggestions = get_query_suggestions("back pain")
    print(f"\nSuggestions with 12 interactions: {suggestions}")

    assert isinstance(suggestions, dict)
    assert len(suggestions) > 0, \
        "Should return suggestions after 10+ interactions"
    assert "prefer_terms" in suggestions or "avoid_terms" in suggestions


def test_format_suggestions_for_prompt():
    suggestions = {
        "prefer_terms": ["Aerobic Exercise"],
        "avoid_terms": ["Mobility Limitation"],
        "add_filter": "Randomized Controlled Trial"
    }
    formatted = format_suggestions_for_prompt(suggestions)
    print(f"\nFormatted:\n{formatted}")

    assert "Aerobic Exercise" in formatted
    assert "Mobility Limitation" in formatted
    assert "Randomized Controlled Trial" in formatted


def test_format_empty_suggestions_returns_empty_string():
    formatted = format_suggestions_for_prompt({})
    assert formatted == "", f"Expected empty string, got: '{formatted}'"
    print("\nEmpty suggestions correctly returns empty string")


def test_cold_start_returns_no_suggestions():
    _reset_db()
    result = suggest_query_improvements("does walking help back pain")
    print(f"\nCold start suggestions: {result}")
    assert result == {}, "Cold start should return empty dict"


def test_record_user_interaction_via_agent():
    _reset_db()
    record_user_interaction(
        session_id="sess_test",
        pmid="12345678",
        action="clicked",
        query_string="exercise depression teenagers",
        mesh_terms=["Exercise", "Depression", "Adolescent"]
    )

    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interactions WHERE pmid = '12345678'")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    print(f"\nInteraction recorded via agent: {tuple(row)}")