import json
import pytest
from pathlib import Path
from core.pubmed_client import lookup_mesh_term
from agents.agent1_interpreter import PICOResult
from agents.agent2_mesh_suggester import suggest_mesh, MeSHResult

CACHE_PATH = Path("data/mesh_terms.json")

def test_heart_attack_maps_to_myocardial_infarction():
    result = lookup_mesh_term("heart attack")
    print(f"\nMeSH for 'heart attack': {result}")

    assert isinstance(result, list)
    assert len(result) > 0, "Should return at least one MeSH term"

    all_terms = " ".join(result).lower()
    assert "myocardial infarction" in all_terms or "myocardial" in all_terms, \
        f"Expected 'Myocardial Infarction' in results, got: {result}"

def test_kids_maps_to_child_or_adolescent():
    result = lookup_mesh_term("kids")
    print(f"\nMeSH for 'kids': {result}")

    assert isinstance(result, list)
    assert len(result) > 0, "Should return at least one MeSH term"

    all_terms = " ".join(result).lower()
    assert "child" in all_terms or "adolescent" in all_terms or "pediatric" in all_terms, \
        f"Expected child/adolescent/pediatric in results, got: {result}"

def test_walking_maps_to_walking():
    result = lookup_mesh_term("walking")
    print(f"\nMeSH for 'walking': {result}")

    assert isinstance(result, list)
    assert len(result) > 0, "Should return at least one MeSH term"

    all_terms = " ".join(result).lower()
    assert "walking" in all_terms or "gait" in all_terms, \
        f"Expected 'Walking' or 'Gait' in results, got: {result}"

def test_cache_grows_after_lookup():
    # clear the specific term from cache first
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r") as f:
            cache = json.load(f)
        cache.pop("cancer treatment", None)
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f)

    lookup_mesh_term("cancer treatment")

    with open(CACHE_PATH, "r") as f:
        cache = json.load(f)

    assert "cancer treatment" in cache, "Cache should contain the newly looked up term"
    print(f"\nCache entry for 'cancer treatment': {cache['cancer treatment']}")

def test_full_pipeline_pico_to_mesh():
    pico = PICOResult(
        population="teenagers",
        intervention="exercise",
        comparison=None,
        outcome="depression",
        original_query="Does exercise help depressed teenagers?"
    )
    result = suggest_mesh(pico)
    print(f"\nFull MeSHResult: {result}")

    assert isinstance(result, MeSHResult)
    assert len(result.original_terms) > 0
    assert len(result.mesh_mappings) > 0
    assert all(isinstance(v, list) for v in result.mesh_mappings.values())
    assert all(0.0 <= v <= 1.0 for v in result.confidence.values())






    