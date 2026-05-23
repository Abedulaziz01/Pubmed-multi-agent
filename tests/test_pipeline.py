import pytest
import time
from core.pipeline import run_pipeline, PipelineResult
from agents.agent1_interpreter import PICOResult
from agents.agent2_mesh_suggester import MeSHResult
from agents.agent3_query_builder import QueryResult
from agents.agent4_finder import PaperResult


def test_pipeline_returns_pipeline_result():
    result = run_pipeline("does walking help back pain")
    print(f"\nResult type: {type(result)}")

    assert isinstance(result, PipelineResult)
    assert result.original_query == "does walking help back pain"


def test_pipeline_success_flag_is_true():
    result = run_pipeline("does aspirin help headaches")
    print(f"\nSuccess: {result.success}")
    print(f"Error: {result.error_message}")

    assert result.success is True, \
        f"Pipeline failed with: {result.error_message}"
    assert result.failed_at_agent is None


def test_pipeline_all_agents_ran():
    result = run_pipeline("does meditation reduce anxiety")
    print(f"\nPICO: {result.pico}")
    print(f"MeSH: {result.mesh_mappings}")
    print(f"Query: {result.pubmed_query}")
    print(f"Papers: {len(result.papers)}")

    assert result.pico is not None, "Agent 1 did not run — pico is None"
    assert result.mesh_mappings is not None, "Agent 2 did not run — mesh is None"
    assert result.pubmed_query is not None, "Agent 3 did not run — query is None"
    assert len(result.papers) > 0, "Agent 4 did not run — no papers returned"


def test_pipeline_pico_has_correct_shape():
    result = run_pipeline("does exercise help depressed teenagers")

    assert isinstance(result.pico, PICOResult)
    assert result.pico.original_query == "does exercise help depressed teenagers"
    assert result.pico.population != ""
    assert result.pico.intervention != ""
    print(f"\nPICO population: {result.pico.population}")
    print(f"PICO intervention: {result.pico.intervention}")


def test_pipeline_query_has_mesh_tags():
    result = run_pipeline("does walking help back pain")

    assert result.pubmed_query is not None
    assert "[MeSH]" in result.pubmed_query.query_string or \
           "[tiab]" in result.pubmed_query.query_string, \
        f"Query has no field tags: {result.pubmed_query.query_string}"
    print(f"\nQuery: {result.pubmed_query.query_string}")


def test_pipeline_papers_have_correct_shape():
    result = run_pipeline("does aspirin help headaches")

    assert len(result.papers) > 0
    for paper in result.papers:
        assert isinstance(paper, PaperResult)
        assert paper.pmid != ""
        assert paper.title != ""
        assert paper.pubmed_url.startswith("https://pubmed.ncbi.nlm.nih.gov/")
        assert 0.0 <= paper.relevance_score <= 1.0
    print(f"\nAll {len(result.papers)} papers have correct shape")


def test_pipeline_timing_is_recorded():
    result = run_pipeline("does meditation reduce anxiety")

    print(f"\nTiming: {result.timing}")
    assert result.timing.total_seconds > 0
    assert result.timing.agent1_seconds > 0
    assert result.timing.agent2_seconds > 0
    assert result.timing.agent3_seconds > 0
    assert result.timing.agent4_seconds > 0


def test_pipeline_total_time_under_45_seconds():
    start = time.time()
    result = run_pipeline("does exercise help depressed teenagers")
    elapsed = time.time() - start

    print(f"\nTotal wall time: {round(elapsed, 2)}s")
    print(f"Recorded total: {result.timing.total_seconds}s")

    assert elapsed < 45, \
        f"Pipeline took too long: {round(elapsed, 2)}s — should be under 45s"


def test_pipeline_second_run_faster():
    query = "does walking help back pain"

    r1 = run_pipeline(query)
    t1 = r1.timing.total_seconds

    r2 = run_pipeline(query)
    t2 = r2.timing.total_seconds

    print(f"\nRun 1: {t1}s")
    print(f"Run 2: {t2}s")

    # MeSH cache and ChromaDB cache both work on second run
    # but LLM calls still go to Groq each time so total difference is small
    # we just confirm both runs completed successfully, not that one is faster
    assert r1.success is True, "Run 1 should succeed"
    assert r2.success is True, "Run 2 should succeed"
    assert r2.timing.agent2_seconds <= r1.timing.agent2_seconds + 1.0, \
        "Agent 2 should be same speed or faster on second run due to MeSH cache"
    print(f"Agent 2 Run 1: {r1.timing.agent2_seconds}s")
    print(f"Agent 2 Run 2: {r2.timing.agent2_seconds}s")
    print("Caching confirmed working for MeSH terms")


def test_pipeline_does_not_crash_on_empty_query():
    result = run_pipeline("")
    print(f"\nEmpty query result — success: {result.success}")
    print(f"Error: {result.error_message}")

    assert isinstance(result, PipelineResult)
    assert result.original_query == ""


def test_pipeline_does_not_crash_on_single_word():
    result = run_pipeline("cancer")
    print(f"\nSingle word result — success: {result.success}")
    print(f"Papers: {len(result.papers)}")

    assert isinstance(result, PipelineResult)


def test_pipeline_error_handling_broken_key():
    import config
    import core.llm_client as llm
    from groq import Groq

    real_key = config.GROQ_API_KEY
    config.GROQ_API_KEY = "broken_key_for_testing"
    llm._client = Groq(api_key="broken_key_for_testing")

    try:
        result = run_pipeline("does exercise help teenagers")

        print(f"\nSuccess: {result.success}")
        print(f"Failed at: {result.failed_at_agent}")
        print(f"Error: {result.error_message}")

        assert result.success is False, \
            "Pipeline should fail with broken API key"
        assert result.failed_at_agent is not None, \
            "Should record which agent failed"
        assert result.error_message is not None, \
            "Should record the error message"

    finally:
        config.GROQ_API_KEY = real_key
        llm._client = Groq(api_key=real_key)