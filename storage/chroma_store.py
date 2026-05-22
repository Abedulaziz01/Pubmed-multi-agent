import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import config

EMBED_MODEL = "all-MiniLM-L6-v2"

_chroma_client = None
_embedding_fn = None


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        Path(config.CHROMA_PERSIST_DIR).mkdir(exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIR
        )
    return _chroma_client


def _get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        print("[ChromaDB] Loading embedding model (first time is slow)...")
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
        print("[ChromaDB] Embedding model loaded")
    return _embedding_fn


def index_abstracts(papers: list[dict], query_id: str) -> str:
    if not papers:
        print("[ChromaDB] No papers to index")
        return query_id

    client = _get_client()
    embed_fn = _get_embedding_fn()

    collection_name = f"pubmed_{query_id}"[:63]

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )

    documents = []
    metadatas = []
    ids = []

    for paper in papers:
        text = f"{paper['title']} {paper['abstract']}"
        documents.append(text)
        metadatas.append({
            "pmid": paper["pmid"],
            "title": paper["title"],
            "year": str(paper["year"]),
            "pubmed_url": paper["pubmed_url"],
            "abstract": paper["abstract"][:1000]
        })
        ids.append(paper["pmid"])

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"[ChromaDB] Indexed {len(papers)} papers into '{collection_name}'")
    return collection_name


def rank_by_relevance(
    user_query: str,
    collection_name: str,
    top_k: int = 10
) -> list[dict]:
    client = _get_client()
    embed_fn = _get_embedding_fn()

    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embed_fn
        )
    except Exception as e:
        print(f"[ChromaDB] Collection not found: {e}")
        return []

    results = collection.query(
        query_texts=[user_query],
        n_results=min(top_k, collection.count())
    )

    ranked = []
    if results and results["metadatas"]:
        for i, metadata in enumerate(results["metadatas"][0]):
            distance = results["distances"][0][i]
            relevance_score = round(1 - distance, 4)
            ranked.append({
                "pmid": metadata["pmid"],
                "title": metadata["title"],
                "year": int(metadata.get("year", 0)),
                "pubmed_url": metadata["pubmed_url"],
                "abstract": metadata["abstract"],
                "relevance_score": relevance_score
            })

    print(f"[ChromaDB] Ranked {len(ranked)} papers by relevance")
    return ranked