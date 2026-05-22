import hashlib
from pydantic import BaseModel
from core.pubmed_client import search_pubmed, fetch_abstracts
from storage.chroma_store import index_abstracts, rank_by_relevance
from core.llm_client import call_llm
from agents.agent3_query_builder import QueryResult
import config


class PaperResult(BaseModel):
    pmid: str
    title: str
    abstract: str
    year: int
    highlighted_sentences: list[str]
    relevance_score: float
    pubmed_url: str


HIGHLIGHTER_PROMPT = """You are a medical research assistant.

Your job is to read a paper abstract and find 1 to 3 sentences that most directly answer the user's question.

Rules:
- Return ONLY valid JSON. No explanation. No markdown. No code fences.
- Format: {"highlighted": ["sentence one", "sentence two"]}
- Only return sentences that are actually in the abstract word for word
- If no sentence directly answers the question, return {"highlighted": []}
- Maximum 3 sentences
"""


def _make_query_id(query_string: str) -> str:
    return hashlib.md5(query_string.encode()).hexdigest()[:12]


def _highlight_sentences(abstract: str, question: str) -> list[str]:
    user_prompt = f"""User question: {question}

Abstract:
{abstract}

Find 1-3 sentences from this abstract that directly answer the question.
Return JSON only: {{"highlighted": ["sentence 1", "sentence 2"]}}"""

    response = call_llm(HIGHLIGHTER_PROMPT, user_prompt)

    try:
        import json
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]).strip()
        data = json.loads(cleaned)
        return data.get("highlighted", [])
    except Exception as e:
        print(f"[Agent 4] Highlight parse failed: {e}")
        return []


def find_papers(
    query_result: QueryResult,
    original_question: str
) -> list[PaperResult]:

    print(f"\n[Agent 4] Starting search for: {original_question}")

    # step 1 — search pubmed and fetch abstracts
    pmids = search_pubmed(
        query_result.query_string,
        max_results=config.MAX_PUBMED_RESULTS
    )

    if not pmids:
        print("[Agent 4] No PMIDs returned — query may be too narrow")
        return []

    papers = fetch_abstracts(pmids)

    if not papers:
        print("[Agent 4] No abstracts fetched")
        return []

    # step 2 — index into chromadb and rank by relevance
    query_id = _make_query_id(query_result.query_string)
    collection_name = index_abstracts(papers, query_id)
    ranked = rank_by_relevance(original_question, collection_name, top_k=10)

    if not ranked:
        print("[Agent 4] Ranking returned no results")
        return []

    # step 3 — highlight sentences for top 10 results
    print(f"\n[Agent 4] Highlighting sentences for top {len(ranked)} papers...")
    results = []

    for i, paper in enumerate(ranked):
        print(f"[Agent 4] Highlighting paper {i+1}/{len(ranked)}: {paper['title'][:50]}...")

        highlighted = _highlight_sentences(
            abstract=paper["abstract"],
            question=original_question
        )

        results.append(PaperResult(
            pmid=paper["pmid"],
            title=paper["title"],
            abstract=paper["abstract"],
            year=paper["year"],
            highlighted_sentences=highlighted,
            relevance_score=paper["relevance_score"],
            pubmed_url=paper["pubmed_url"]
        ))

    print(f"\n[Agent 4] Done. Returning {len(results)} annotated papers")
    return results