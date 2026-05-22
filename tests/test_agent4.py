import pytest
from agents.agent3_query_builder import QueryResult
from agents.agent4_finder import find_papers, PaperResult
from core.pubmed_client import search_pubmed, fetch_abstracts


def test_search_returns_pmids():
    pmids = search_pubmed("exercise depression adolescents", max_results=10)
    print(f"\nPMIDs returned: {pmids}")

    assert isinstance(pmids, list)
    assert len(pmids) >= 5, \
        f"Expected at least 5 results, got {len(pmids)}"
    assert all(p.isdigit() for p in pmids), \
        "All PMIDs should be numeric strings"


def test_fetch_abstracts_returns_papers():
    pmids = search_pubmed("exercise depression adolescents", max_results=5)
    papers = fetch_abstracts(pmids)
    print(f"\nPapers fetched: {len(papers)}")

    assert len(papers) >= 1
    for paper in papers:
        assert "pmid" in paper
        assert "title" in paper
        assert "abstract" in paper
        assert "pubmed_url" in paper
        assert paper["pubmed_url"].startswith("https://pubmed.ncbi.nlm.nih.gov/")


def test_pubmed_url_format():
    pmids = search_pubmed("walking back pain", max_results=3)
    papers = fetch_abstracts(pmids)

    for paper in papers:
        expected_url = f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/"
        assert paper["pubmed_url"] == expected_url, \
            f"URL format wrong: {paper['pubmed_url']}"
    print("\nAll URLs in correct format")


def test_find_papers_returns_results():
    query = QueryResult(
        query_string='("Exercise"[MeSH] OR "physical activity"[tiab]) AND ("Depression"[MeSH]) AND ("Adolescent"[MeSH])',
        field_tags=["[MeSH]", "[tiab]"],
        estimated_complexity="complex"
    )
    papers = find_papers(query, "Does exercise help depressed teenagers?")
    print(f"\nPapers returned: {len(papers)}")

    assert len(papers) >= 3, \
        f"Expected at least 3 results, got {len(papers)}"
    assert all(isinstance(p, PaperResult) for p in papers)


def test_highlighted_sentences_not_empty():
    query = QueryResult(
        query_string='("Exercise"[MeSH] OR "physical activity"[tiab]) AND ("Depression"[MeSH]) AND ("Adolescent"[MeSH])',
        field_tags=["[MeSH]", "[tiab]"],
        estimated_complexity="complex"
    )
    papers = find_papers(query, "Does exercise help depressed teenagers?")

    papers_with_highlights = [p for p in papers if p.highlighted_sentences]
    print(f"\nPapers with highlights: {len(papers_with_highlights)}/{len(papers)}")

    assert len(papers_with_highlights) >= 3, \
        "At least 3 papers should have highlighted sentences"


def test_relevance_scores_between_0_and_1():
    query = QueryResult(
        query_string='("Exercise"[MeSH]) AND ("Depression"[MeSH]) AND ("Adolescent"[MeSH])',
        field_tags=["[MeSH]"],
        estimated_complexity="complex"
    )
    papers = find_papers(query, "Does exercise help depressed teenagers?")

    for paper in papers:
        assert 0.0 <= paper.relevance_score <= 1.0, \
            f"Score out of range: {paper.relevance_score}"
    print(f"\nAll {len(papers)} relevance scores are between 0 and 1")