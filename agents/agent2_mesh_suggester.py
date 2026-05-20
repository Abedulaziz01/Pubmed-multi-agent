from pydantic import BaseModel
from typing import Optional
from core.pubmed_client import lookup_mesh_term
from core.llm_client import call_llm
from agents.agent1_interpreter import PICOResult

class MeSHResult(BaseModel):
    original_terms: list[str]
    mesh_mappings: dict[str, list[str]]
    confidence: dict[str, float]

MESH_FALLBACK_PROMPT = """You are a medical librarian expert in MeSH (Medical Subject Headings).

Given a plain English medical term, return the official MeSH term(s) that best match it.

Rules:
- Return ONLY valid JSON. No explanation, no markdown, no code fences.
- Format: {"mesh_terms": ["Term1", "Term2"]}
- Return 1 to 3 MeSH terms maximum
- Use official MeSH vocabulary only
- If truly unknown, return {"mesh_terms": []}

Example input: heart attack
Example output: {"mesh_terms": ["Myocardial Infarction"]}
"""

def _llm_fallback(term: str) -> list[str]:
    print(f"[Agent 2] LLM fallback for term: '{term}'")
    response = call_llm(MESH_FALLBACK_PROMPT, term)
    print(f"[Agent 2] LLM response: {response}")

    try:
        import json
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        data = json.loads(cleaned)
        return data.get("mesh_terms", [])
    except Exception as e:
        print(f"[Agent 2] LLM fallback parse failed: {e}")
        return []

def _score_confidence(term: str, mesh_terms: list[str]) -> float:
    if not mesh_terms:
        return 0.0
    # exact match scores highest
    term_lower = term.lower()
    for m in mesh_terms:
        if m.lower() == term_lower:
            return 1.0
    # partial match scores medium
    for m in mesh_terms:
        if term_lower in m.lower() or m.lower() in term_lower:
            return 0.8
    # found something but no overlap
    return 0.6

def _extract_terms_from_pico(pico: PICOResult) -> list[str]:
    terms = []
    for field in [pico.population, pico.intervention, pico.comparison, pico.outcome]:
        if field and field.strip():
            # split multi-word fields into individual concepts
            terms.append(field.strip())
    return list(set(terms))  # deduplicate

def suggest_mesh(pico: PICOResult) -> MeSHResult:
    terms = _extract_terms_from_pico(pico)
    print(f"\n[Agent 2] Terms extracted from PICO: {terms}")

    mesh_mappings = {}
    confidence = {}

    for term in terms:
        # step 1: try NCBI API
        mesh_terms = lookup_mesh_term(term)

        # step 2: if NCBI returns nothing, fall back to LLM
        if not mesh_terms:
            mesh_terms = _llm_fallback(term)

        mesh_mappings[term] = mesh_terms
        confidence[term] = _score_confidence(term, mesh_terms)
        print(f"[Agent 2] '{term}' → {mesh_terms} (confidence: {confidence[term]})")

    return MeSHResult(
        original_terms=terms,
        mesh_mappings=mesh_mappings,
        confidence=confidence
    )