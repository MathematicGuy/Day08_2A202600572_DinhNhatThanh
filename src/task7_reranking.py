"""Task 7 - Reranking."""

import os

import requests

from .local_index import cosine_similarity, hash_embedding, tokenize


def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Local relevance reranker used when no external cross-encoder is configured."""
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return candidates[:top_k]

    reranked = []
    for item in candidates:
        doc_tokens = set(tokenize(item.get("content", "")))
        overlap = len(query_tokens & doc_tokens) / max(1, len(query_tokens))
        original_score = float(item.get("score", 0.0))
        score = 0.65 * overlap + 0.35 * original_score
        updated = item.copy()
        updated["score"] = float(score)
        reranked.append(updated)

    reranked.sort(key=lambda item: item["score"], reverse=True)
    return reranked[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    selected: list[int] = []
    remaining = list(range(len(candidates)))

    while remaining and len(selected) < top_k:
        best_idx = remaining[0]
        best_score = float("-inf")
        for idx in remaining:
            doc_embedding = candidates[idx].get("embedding") or hash_embedding(candidates[idx]["content"])
            relevance = cosine_similarity(query_embedding, doc_embedding)
            diversity_penalty = 0.0
            for selected_idx in selected:
                selected_embedding = candidates[selected_idx].get("embedding") or hash_embedding(
                    candidates[selected_idx]["content"]
                )
                diversity_penalty = max(diversity_penalty, cosine_similarity(doc_embedding, selected_embedding))
            score = lambda_param * relevance - (1 - lambda_param) * diversity_penalty
            if score > best_score:
                best_idx = idx
                best_score = score
        selected.append(best_idx)
        remaining.remove(best_idx)

    return [candidates[i] for i in selected]


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            metadata = item.get("metadata", {})
            key = f"{metadata.get('path', '')}#{metadata.get('chunk_index', '')}" or item.get("content", "")
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            items[key] = item

    merged = []
    for key, score in sorted(scores.items(), key=lambda pair: pair[1], reverse=True)[:top_k]:
        item = items[key].copy()
        item["score"] = float(score)
        merged.append(item)
    return merged


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",
) -> list[dict]:
    if not candidates:
        return []
    if method == "jina":
        return rerank_jina_api(query, candidates, top_k=top_k)
    if method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    if method == "mmr":
        return rerank_mmr(hash_embedding(query), candidates, top_k=top_k)
    return rerank_cross_encoder(query, candidates, top_k=top_k)


def rerank_jina_api(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Use Jina hosted rerank when configured; otherwise use local reranking."""
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        return rerank_cross_encoder(query, candidates, top_k=top_k)

    response = requests.post(
        "https://api.jina.ai/v1/rerank",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": os.getenv("JINA_RERANKER_MODEL", "jinaai/jina-reranker-v2-base-multilingual"),
            "query": query,
            "documents": [candidate.get("content", "") for candidate in candidates],
            "top_n": top_k,
            "return_documents": False,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    reranked = []
    for result in payload.get("results", [])[:top_k]:
        idx = result.get("index")
        if idx is None or idx >= len(candidates):
            continue
        item = candidates[idx].copy()
        item["score"] = float(result.get("relevance_score", result.get("score", item.get("score", 0.0))))
        item["metadata"] = {**item.get("metadata", {}), "reranker": "jina"}
        reranked.append(item)
    return reranked or rerank_cross_encoder(query, candidates, top_k=top_k)


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Dieu 249: Toi tang tru trai phep chat ma tuy", "score": 0.8, "metadata": {}},
        {"content": "Nghe si bi bat vi su dung ma tuy", "score": 0.7, "metadata": {}},
    ]
    for r in rerank("hinh phat tang tru ma tuy", dummy_candidates, top_k=2):
        print(f"[{r['score']:.3f}] {r['content']}")
