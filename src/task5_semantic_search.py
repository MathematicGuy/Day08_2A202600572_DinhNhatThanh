"""Task 5 - Semantic search over the local index."""

from .local_index import cosine_similarity, ensure_chunks, hash_embedding, metadata_matches
from .task4_chunking_indexing import EMBEDDING_DIM, EMBEDDING_MODEL

_MODEL = None


def _embed_query(query: str) -> list[float]:
    global _MODEL
    try:
        from sentence_transformers import SentenceTransformer

        if _MODEL is None:
            _MODEL = SentenceTransformer(EMBEDDING_MODEL)
        return _MODEL.encode([query], normalize_embeddings=True)[0].tolist()
    except Exception:
        return hash_embedding(query, EMBEDDING_DIM)


def semantic_search(query: str, top_k: int = 10, filters: dict | None = None) -> list[dict]:
    """Return chunks sorted by vector similarity score."""
    if top_k <= 0:
        return []

    chunks = ensure_chunks()
    query_embedding = _embed_query(query)
    results = []
    for chunk in chunks:
        if not metadata_matches(chunk.get("metadata", {}), filters):
            continue
        score = cosine_similarity(query_embedding, chunk.get("embedding", []))
        results.append(
            {
                "content": chunk["content"],
                "score": float(score),
                "metadata": chunk.get("metadata", {}),
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for r in semantic_search("hinh phat cho toi tang tru ma tuy", top_k=5):
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
