from pydantic import BaseModel
from typing import Optional
from core.llm_client import call_llm
from agents.agent1_interpreter import PICOResult
from agents.agent2_mesh_suggester import MeSHResult


class QueryResult(BaseModel):
    query_string: str
    field_tags: list[str]
    estimated_complexity: str  # "simple", "medium", or "complex"


def is_balanced(query: str) -> bool:
    count = 0
    for char in query:
        if char == "(":
            count += 1
        elif char == ")":
            count -= 1
        if count < 0:
            return False
    return count == 0


def _estimate_complexity(query: str) -> str:
    and_count = query.upper().count(" AND ")
    or_count = query.upper().count(" OR ")
    mesh_count = query.count("[MeSH]")

    if and_count >= 3 or mesh_count >= 4:
        return "complex"
    elif and_count >= 2 or or_count >= 2:
        return "medium"
    else:
        return "simple"


def _extract_field_tags(query: str) -> list[str]:
    tags = []
    if "[MeSH]" in query:
        tags.append("[MeSH]")
    if "[tiab]" in query:
        tags.append("[tiab]")
    if "[pt]" in query:
        tags.append("[pt]")
    return tags


def _clean_llm_output(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]).strip()
    return cleaned


QUERY_BUILDER_PROMPT = """You are a PubMed search expert. Your job is to build a valid PubMed query string.

PubMed query rules you must follow:
1. MeSH terms use the [MeSH] tag: "Depression"[MeSH]
2. Free text terms use the [tiab] tag (searches title and abstract): "depression"[tiab]
3. Within one concept, connect synonyms with OR inside parentheses:
   ("Depression"[MeSH] OR "depression"[tiab] OR "depressive disorder"[tiab])
4. Across different concepts, connect with AND:
   (concept A) AND (concept B) AND (concept C)
5. Every term MUST have a field tag. Never write a bare word like: depression
6. Always wrap each concept group in parentheses
7. If the study type is clearly a clinical comparison, add: AND "Randomized Controlled Trial"[pt]

You will receive:
- PICO components (Population, Intervention, Comparison, Outcome)
- MeSH term mappings for each plain English term

Your output must be ONLY the raw query string. No explanation. No markdown. No code fences.
Just the query string itself, ready to paste into PubMed.

Example output:
("Adolescent"[MeSH] OR "teenager"[tiab]) AND ("Exercise"[MeSH] OR "physical activity"[tiab]) AND ("Depression"[MeSH] OR "depressive disorder"[tiab])
"""

def _clean_query(query: str) -> str:
    import re

    # fix AND inside parentheses between two MeSH/tiab terms — replace with OR
    # pattern: ("X"[tag] AND "Y"[tag])
    def fix_inner_and(match):
        inner = match.group(1)
        if inner.count("[MeSH]") + inner.count("[tiab]") >= 2:
            fixed = re.sub(r'\bAND\b', 'OR', inner)
            return f"({fixed})"
        return match.group(0)

    query = re.sub(r'\(([^()]+)\)', fix_inner_and, query)

    # remove duplicate concept blocks
    # split by AND, deduplicate, rejoin
    blocks = [b.strip() for b in query.split(" AND ")]
    seen = []
    for block in blocks:
        normalized = block.lower().strip("() ")
        if normalized not in [s.lower().strip("() ") for s in seen]:
            seen.append(block)

    return " AND ".join(seen)
def build_query(pico: PICOResult, mesh_result: MeSHResult) -> QueryResult:
    print(f"\n[Agent 3] Building query for: {pico.original_query}")

    mesh_summary = ""
    for term, mappings in mesh_result.mesh_mappings.items():
        mesh_summary += f"  Plain term: '{term}' -> MeSH terms: {mappings}\n"

    user_prompt = f"""Build a PubMed query for this research question:

Original question: {pico.original_query}

PICO breakdown:
- Population: {pico.population}
- Intervention: {pico.intervention}
- Comparison: {pico.comparison if pico.comparison else 'none'}
- Outcome: {pico.outcome}

MeSH term mappings:
{mesh_summary}

Return only the query string. Nothing else."""

    raw_response = call_llm(QUERY_BUILDER_PROMPT, user_prompt)
    print(f"[Agent 3] Raw LLM output: {raw_response}")

    query_string = _clean_llm_output(raw_response)

    has_tag = "[MeSH]" in query_string or "[tiab]" in query_string
    if not has_tag:
        print("[Agent 3] No field tags found — retrying with stricter prompt")

        retry_prompt = f"""The query you returned had no PubMed field tags like [MeSH] or [tiab].

Original question: {pico.original_query}

You MUST return a query where every term has a field tag.
Example of correct format: ("Depression"[MeSH] OR "depression"[tiab]) AND ("Exercise"[MeSH])

Return only the corrected query string now:"""

        raw_retry = call_llm(QUERY_BUILDER_PROMPT, retry_prompt)
        query_string = _clean_llm_output(raw_retry)
        print(f"[Agent 3] Retry output: {query_string}")

    if not is_balanced(query_string):
        print(f"[Agent 3] WARNING: Unbalanced parentheses detected in query")

    field_tags = _extract_field_tags(query_string)
    complexity = _estimate_complexity(query_string)

    print(f"[Agent 3] Final query: {query_string}")
    print(f"[Agent 3] Tags: {field_tags} | Complexity: {complexity}")

    return QueryResult(
        query_string=query_string,
        field_tags=field_tags,
        estimated_complexity=complexity
    )