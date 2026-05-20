import json
import time
import requests
from pathlib import Path
import config

CACHE_PATH = Path("data/mesh_terms.json")

def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    return {}

def _save_cache(cache: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def _llm_fallback_mesh(term: str, call_llm_fn) -> list[str]:
    prompt = f"""Return the official MeSH (Medical Subject Headings) term for: "{term}"
Return ONLY valid JSON, no markdown, no explanation.
Format: {{"mesh_terms": ["Term1", "Term2"]}}
If unknown return {{"mesh_terms": []}}"""

    response = call_llm_fn(
        "You are a medical librarian expert in MeSH vocabulary.",
        prompt
    )
    try:
        cleaned = response.strip().strip("```json").strip("```").strip()
        return json.loads(cleaned).get("mesh_terms", [])
    except Exception:
        return []

def lookup_mesh_term(plain_term: str) -> list[str]:
    term_lower = plain_term.lower().strip()

    # check cache first
    cache = _load_cache()
    if term_lower in cache:
        print(f"[Cache HIT] '{term_lower}' found in cache — skipping NCBI call")
        return cache[term_lower]

    print(f"[Cache MISS] '{term_lower}' not in cache — calling NCBI API")

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "mesh",
        "term": plain_term,
        "retmode": "json",
        "retmax": 3,
        "email": config.NCBI_EMAIL
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        id_list = data.get("esearchresult", {}).get("idlist", [])

        if not id_list:
            print(f"[NCBI] No MeSH IDs found for '{plain_term}' — trying LLM fallback")
            from core.llm_client import call_llm
            mesh_terms = _llm_fallback_mesh(plain_term, call_llm)
            cache[term_lower] = mesh_terms
            _save_cache(cache)
            return mesh_terms

        mesh_terms = _fetch_mesh_names(id_list)

        cache[term_lower] = mesh_terms
        _save_cache(cache)

        time.sleep(0.34)  # NCBI rate limit: max 3 requests/second
        return mesh_terms

    except requests.RequestException as e:
        print(f"[NCBI] Request failed for '{plain_term}': {e}")
        return []

def _fetch_mesh_names(id_list: list[str]) -> list[str]:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "mesh",
        "id": ",".join(id_list),
        "retmode": "json",
        "email": config.NCBI_EMAIL
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        names = []
        result = data.get("result", {})
        for uid in id_list:
            if uid in result:
                name = result[uid].get("ds_meshterms", [])
                if name:
                    names.append(name[0])
                else:
                    raw = result[uid].get("ds_name", "")
                    if raw:
                        names.append(raw)

        return names

    except requests.RequestException as e:
        print(f"[NCBI] esummary failed: {e}")
        return []