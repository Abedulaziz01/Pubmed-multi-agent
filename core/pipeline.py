import time
from pydantic import BaseModel
from typing import Optional

from agents.agent1_interpreter import extract_pico, PICOResult
from agents.agent2_mesh_suggester import suggest_mesh, MeSHResult
from agents.agent3_query_builder import build_query, QueryResult
from agents.agent4_finder import find_papers, PaperResult


class AgentTiming(BaseModel):
    agent1_seconds: float = 0.0
    agent2_seconds: float = 0.0
    agent3_seconds: float = 0.0
    agent4_seconds: float = 0.0
    total_seconds: float = 0.0


class PipelineResult(BaseModel):
    original_query: str
    pico: Optional[PICOResult] = None
    mesh_mappings: Optional[MeSHResult] = None
    pubmed_query: Optional[QueryResult] = None
    papers: list[PaperResult] = []
    timing: AgentTiming = AgentTiming()
    success: bool = True
    error_message: Optional[str] = None
    failed_at_agent: Optional[str] = None


def run_pipeline(user_query: str) -> PipelineResult:
    print(f"\n{'='*60}")
    print(f"[Pipeline] Starting for query: {user_query}")
    print(f"{'='*60}")

    result = PipelineResult(original_query=user_query)
    pipeline_start = time.time()

    # --- Agent 1: PICO Extractor ---
    try:
        print("\n[Pipeline] Running Agent 1: PICO Extractor...")
        t0 = time.time()
        pico = extract_pico(user_query)
        result.pico = pico
        result.timing.agent1_seconds = round(time.time() - t0, 2)
        print(f"[Pipeline] Agent 1 done in {result.timing.agent1_seconds}s")
        print(f"[Pipeline] PICO: population={pico.population} | intervention={pico.intervention}")

    except Exception as e:
        result.success = False
        result.failed_at_agent = "Agent 1: PICO Extractor"
        result.error_message = f"Agent 1 failed: {str(e)}"
        result.timing.total_seconds = round(time.time() - pipeline_start, 2)
        print(f"[Pipeline] ERROR in Agent 1: {e}")
        return result

    # --- Agent 2: MeSH Suggester ---
    try:
        print("\n[Pipeline] Running Agent 2: MeSH Suggester...")
        t0 = time.time()
        mesh = suggest_mesh(pico)
        result.mesh_mappings = mesh
        result.timing.agent2_seconds = round(time.time() - t0, 2)
        print(f"[Pipeline] Agent 2 done in {result.timing.agent2_seconds}s")
        print(f"[Pipeline] MeSH mappings: {list(mesh.mesh_mappings.keys())}")

    except Exception as e:
        result.success = False
        result.failed_at_agent = "Agent 2: MeSH Suggester"
        result.error_message = f"Agent 2 failed: {str(e)}"
        result.timing.total_seconds = round(time.time() - pipeline_start, 2)
        print(f"[Pipeline] ERROR in Agent 2: {e}")
        return result

    # --- Agent 3: Query Builder ---
    try:
        print("\n[Pipeline] Running Agent 3: Query Builder...")
        t0 = time.time()
        query = build_query(pico, mesh)
        result.pubmed_query = query
        result.timing.agent3_seconds = round(time.time() - t0, 2)
        print(f"[Pipeline] Agent 3 done in {result.timing.agent3_seconds}s")
        print(f"[Pipeline] Query: {query.query_string[:80]}...")

    except Exception as e:
        result.success = False
        result.failed_at_agent = "Agent 3: Query Builder"
        result.error_message = f"Agent 3 failed: {str(e)}"
        result.timing.total_seconds = round(time.time() - pipeline_start, 2)
        print(f"[Pipeline] ERROR in Agent 3: {e}")
        return result

    # --- Agent 4: Finder ---
    try:
        print("\n[Pipeline] Running Agent 4: Finder...")
        t0 = time.time()
        papers = find_papers(query, user_query)
        result.papers = papers
        result.timing.agent4_seconds = round(time.time() - t0, 2)
        print(f"[Pipeline] Agent 4 done in {result.timing.agent4_seconds}s")
        print(f"[Pipeline] Papers found: {len(papers)}")

    except Exception as e:
        result.success = False
        result.failed_at_agent = "Agent 4: Finder"
        result.error_message = f"Agent 4 failed: {str(e)}"
        result.timing.total_seconds = round(time.time() - pipeline_start, 2)
        print(f"[Pipeline] ERROR in Agent 4: {e}")
        # return partial result — we still have pico, mesh, query even if finder failed
        return result

    result.timing.total_seconds = round(time.time() - pipeline_start, 2)

    print(f"\n{'='*60}")
    print(f"[Pipeline] COMPLETE in {result.timing.total_seconds}s")
    print(f"[Pipeline] Agent times: A1={result.timing.agent1_seconds}s | A2={result.timing.agent2_seconds}s | A3={result.timing.agent3_seconds}s | A4={result.timing.agent4_seconds}s")
    print(f"[Pipeline] Papers returned: {len(result.papers)}")
    print(f"{'='*60}")

    return result