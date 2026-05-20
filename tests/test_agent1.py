import pytest
from agents.agent1_interpreter import extract_pico, PICOResult

def test_exercise_depression_teens():
    result = extract_pico("Does exercise help depressed teenagers?")

    print(f"\nTest 1 result: {result}")

    assert isinstance(result, PICOResult)

    population_lower = result.population.lower()
    assert any(word in population_lower for word in ["teen", "adolescent", "youth", "young"]), \
        f"Expected population to mention teens/adolescents, got: {result.population}"

    assert "exercise" in result.intervention.lower() or "physical" in result.intervention.lower(), \
        f"Expected intervention to mention exercise, got: {result.intervention}"

    assert result.outcome != "", "Outcome should not be empty"
    assert result.original_query == "Does exercise help depressed teenagers?"


def test_aspirin_vs_ibuprofen():
    result = extract_pico("Is aspirin better than ibuprofen for headaches?")

    print(f"\nTest 2 result: {result}")

    assert isinstance(result, PICOResult)

    assert result.comparison is not None, "Comparison should not be None — ibuprofen is the comparator"
    assert "ibuprofen" in result.comparison.lower() or "ibuprofen" in result.intervention.lower(), \
        f"Expected ibuprofen to appear in comparison or intervention, got comparison: {result.comparison}"

    assert "aspirin" in result.intervention.lower() or "aspirin" in result.comparison.lower(), \
        f"Expected aspirin to appear, got: {result.intervention}"


def test_single_word_query():
    result = extract_pico("cancer")

    print(f"\nTest 3 result: {result}")

    assert isinstance(result, PICOResult)

    assert result.population != "", "Population should not be empty even for vague query"
    assert result.intervention != "", "Intervention should not be empty even for vague query"
    assert result.outcome != "", "Outcome should not be empty even for vague query"
    assert result.original_query == "cancer"