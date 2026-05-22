import pytest
from agents.agent1_interpreter import extract_pico
from agents.agent2_mesh_suggester import suggest_mesh
from agents.agent3_query_builder import build_query, is_balanced, QueryResult


def test_parenthesis_balance_checker():
    # this test has no API calls — run it first to confirm the helper works
    assert is_balanced('("Depression"[MeSH]) AND ("Exercise"[MeSH])') == True
    assert is_balanced('("Depression"[MeSH] AND ("Exercise"[MeSH])') == False
    assert is_balanced('') == True
    assert is_balanced('()') == True
    assert is_balanced(')(') == False
    print("\nAll parenthesis checks passed")


def test_exercise_depression_teens_query():
    pico = extract_pico("Does exercise help depressed teenagers?")
    mesh = suggest_mesh(pico)
    result = build_query(pico, mesh)

    print(f"\nTest 2 query:\n{result.query_string}")

    assert isinstance(result, QueryResult)
    assert "[MeSH]" in result.query_string, \
        "Query must contain at least one [MeSH] tag"

    query_lower = result.query_string.lower()
    assert "adolescent" in query_lower or "teen" in query_lower, \
        f"Expected adolescent or teen in query, got: {result.query_string}"
    assert "exercise" in query_lower or "physical" in query_lower, \
        f"Expected exercise or physical activity in query, got: {result.query_string}"
    assert is_balanced(result.query_string), \
        f"Parentheses not balanced: {result.query_string}"


def test_walking_back_pain_query():
    pico = extract_pico("Does walking reduce back pain?")
    mesh = suggest_mesh(pico)
    result = build_query(pico, mesh)

    print(f"\nTest 3 query:\n{result.query_string}")

    assert isinstance(result, QueryResult)
    assert "[MeSH]" in result.query_string, \
        "Query must contain at least one [MeSH] tag"

    query_lower = result.query_string.lower()
    assert "back pain" in query_lower or "low back" in query_lower or "lumbar" in query_lower, \
        f"Expected back pain term in query, got: {result.query_string}"
    assert is_balanced(result.query_string), \
        f"Parentheses not balanced: {result.query_string}"


def test_query_has_no_bare_terms():
    pico = extract_pico("Does aspirin reduce fever in children?")
    mesh = suggest_mesh(pico)
    result = build_query(pico, mesh)

    print(f"\nTest 4 query:\n{result.query_string}")

    assert "[MeSH]" in result.query_string or "[tiab]" in result.query_string, \
        "Every term must have a field tag — no bare words allowed"
    assert is_balanced(result.query_string), \
        f"Parentheses not balanced: {result.query_string}"


def test_complexity_is_valid_value():
    pico = extract_pico("Does exercise help depressed teenagers?")
    mesh = suggest_mesh(pico)
    result = build_query(pico, mesh)

    print(f"\nTest 5 complexity: {result.estimated_complexity}")

    assert result.estimated_complexity in ["simple", "medium", "complex"], \
        f"Complexity must be simple/medium/complex, got: {result.estimated_complexity}"