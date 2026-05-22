import json
import time
import requests
from pathlib import Path
import config

CACHE_PATH = Path("data/mesh_terms.json")


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def lookup_mesh_term(plain_term: str) -> list[str]:
    term_lower = plain_term.lower().strip()

    cache = _load_cache()
    if term_lower in cache:
        print(f"[Cache HIT] '{term_lower}' found in cache")
        return cache[term_lower]

    print(f"[Cache MISS] '{term_lower}' not in cache — calling NCBI")

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "mesh",
        "term": plain_term + "[MeSH Terms]",
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
            print(f"[NCBI] No MeSH IDs found for '{plain_term}'")
            cache[term_lower] = []
            _save_cache(cache)
            return []

        mesh_terms = _fetch_mesh_names(id_list)
        cache[term_lower] = mesh_terms
        _save_cache(cache)
        time.sleep(0.34)
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


def search_pubmed(query: str, max_results: int = 50) -> list[str]:
    print(f"\n[PubMed] Searching with query: {query[:80]}...")

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "email": config.NCBI_EMAIL
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        pmids = data.get("esearchresult", {}).get("idlist", [])
        total = data.get("esearchresult", {}).get("count", "0")
        print(f"[PubMed] Found {total} total results, fetching {len(pmids)} PMIDs")
        return pmids

    except requests.RequestException as e:
        print(f"[PubMed] Search failed: {e}")
        return []


def fetch_abstracts(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []

    print(f"[PubMed] Fetching abstracts for {len(pmids)} papers...")

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
        "email": config.NCBI_EMAIL
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return _parse_pubmed_xml(response.text, pmids)

    except requests.RequestException as e:
        print(f"[PubMed] Fetch abstracts failed: {e}")
        return []


def _parse_pubmed_xml(xml_text: str, pmids: list[str]) -> list[dict]:
    import xml.etree.ElementTree as ET

    papers = []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"[PubMed] XML parse error: {e}")
        return []

    for article in root.findall(".//PubmedArticle"):
        try:
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""

            title_el = article.find(".//ArticleTitle")
            title = title_el.text if title_el is not None else ""
            if title is None:
                title = ""

            abstract_parts = article.findall(".//AbstractText")
            abstract = " ".join(
                (el.text or "") for el in abstract_parts
            ).strip()

            year_el = article.find(".//PubDate/Year")
            year_str = year_el.text if year_el is not None else "0"
            try:
                year = int(year_str)
            except ValueError:
                year = 0

            authors = []
            for author in article.findall(".//Author")[:3]:
                last = author.find("LastName")
                first = author.find("ForeName")
                if last is not None:
                    name = last.text or ""
                    if first is not None:
                        name += f" {first.text or ''}"
                    authors.append(name.strip())

            if pmid and abstract:
                papers.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "year": year,
                    "authors": authors,
                    "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })

        except Exception as e:
            print(f"[PubMed] Skipping one article due to parse error: {e}")
            continue

    print(f"[PubMed] Successfully parsed {len(papers)} papers with abstracts")
    return papers