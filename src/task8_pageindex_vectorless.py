"""Task 8 - PageIndex vectorless RAG with local fallback."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from .local_index import ensure_chunks, metadata_matches, tokenize

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
PAGEINDEX_INDEX_ID = os.getenv("PAGEINDEX_INDEX_ID", "")
PAGEINDEX_API_URL = os.getenv("PAGEINDEX_API_URL", "https://api.pageindex.ai")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """Best-effort upload using the installed PageIndex SDK, when available."""
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("PAGEINDEX_API_KEY is not configured")
    try:
        from pageindex import PageIndex

        client = PageIndex(api_key=PAGEINDEX_API_KEY)
        uploaded = []
        for md_file in STANDARDIZED_DIR.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            result = client.upload(
                content=content,
                metadata={"filename": md_file.name, "type": md_file.parent.name},
            )
            uploaded.append(result)
        return uploaded
    except Exception as exc:
        raise RuntimeError(f"PageIndex upload failed: {exc}") from exc


def _local_vectorless_search(query: str, top_k: int, filters: dict | None = None) -> list[dict]:
    query_tokens = set(tokenize(query))
    results = []
    for chunk in ensure_chunks():
        if not metadata_matches(chunk.get("metadata", {}), filters):
            continue
        doc_tokens = set(tokenize(chunk["content"]))
        score = len(query_tokens & doc_tokens) / max(1, len(query_tokens))
        if score > 0:
            results.append(
                {
                    "content": chunk["content"],
                    "score": float(score),
                    "metadata": chunk.get("metadata", {}),
                    "source": "pageindex",
                }
            )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


def pageindex_search(query: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
    """Query PageIndex if configured; otherwise use a local structural fallback."""
    if top_k <= 0:
        return []

    if PAGEINDEX_API_KEY and PAGEINDEX_INDEX_ID:
        try:
            response = requests.post(
                f"{PAGEINDEX_API_URL.rstrip('/')}/query",
                headers={"Authorization": f"Bearer {PAGEINDEX_API_KEY}"},
                json={"index_id": PAGEINDEX_INDEX_ID, "query": query, "top_k": top_k},
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            raw_results = payload.get("results", payload if isinstance(payload, list) else [])
            results = []
            for item in raw_results[:top_k]:
                results.append(
                    {
                        "content": item.get("text") or item.get("content") or "",
                        "score": float(item.get("score", 0.0)),
                        "metadata": item.get("metadata", {}),
                        "source": "pageindex",
                    }
                )
            if results:
                return results
        except Exception:
            pass

    return _local_vectorless_search(query, top_k, filters=filters)


if __name__ == "__main__":
    for r in pageindex_search("hinh phat su dung ma tuy", top_k=3):
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
