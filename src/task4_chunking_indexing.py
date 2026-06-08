"""Task 4 - Chunking and local indexing."""

import os
from pathlib import Path

import requests

from .local_index import hash_embedding, read_markdown_documents, save_chunks

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Recursive chunking is robust for mixed legal markdown and news articles.
# 500 chars keeps chunks focused; 50 chars overlap preserves citation context.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"
JINA_LATE_CHUNKING_METHOD = "jina_late"

# This lightweight model is easy to run locally. If sentence-transformers or
# weights are unavailable, embed_chunks falls back to deterministic hashing.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
VECTOR_STORE = "local-json"
JINA_EMBEDDING_MODEL = "jina-embeddings-v3"
JINA_EMBEDDING_API_URL = "https://api.jina.ai/v1/embeddings"


def load_documents() -> list[dict]:
    """Read markdown files from data/standardized/."""
    return read_markdown_documents()


def active_chunking_method() -> str:
    return os.getenv("CHUNKING_METHOD", CHUNKING_METHOD).strip().lower() or CHUNKING_METHOD


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Split documents into chunks while preserving metadata."""
    chunks = []
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        split_text = splitter.split_text
    except Exception:
        def split_text(text: str) -> list[str]:
            step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
            return [text[i:i + CHUNK_SIZE] for i in range(0, len(text), step)]

    for doc in documents:
        for i, chunk_text in enumerate(split_text(doc["content"])):
            chunk_text = chunk_text.strip()
            if chunk_text:
                chunks.append(
                    {
                        "content": chunk_text,
                        "metadata": {
                            **doc["metadata"],
                            "chunk_index": i,
                            "chunking_method": active_chunking_method(),
                        },
                    }
                )
    return chunks


def _embed_chunks_with_jina_late(chunks: list[dict]) -> list[dict] | None:
    api_key = os.getenv("JINA_API_KEY")
    if not api_key or not chunks:
        return None

    grouped: dict[str, list[dict]] = {}
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        group_key = metadata.get("path") or metadata.get("source") or "__default__"
        grouped.setdefault(group_key, []).append(chunk)

    model_name = os.getenv("JINA_EMBEDDING_MODEL", JINA_EMBEDDING_MODEL)
    for group_chunks in grouped.values():
        texts = [chunk.get("content", "") for chunk in group_chunks]
        response = requests.post(
            os.getenv("JINA_EMBEDDING_API_URL", JINA_EMBEDDING_API_URL),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model_name,
                "task": "retrieval.passage",
                "late_chunking": True,
                "input": texts,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        embeddings = sorted(payload.get("data", []), key=lambda item: item.get("index", 0))
        if len(embeddings) != len(group_chunks):
            raise ValueError("Jina late chunking returned a mismatched embedding count.")
        for chunk, item in zip(group_chunks, embeddings):
            chunk["embedding"] = item.get("embedding", [])
            chunk["metadata"] = {
                **chunk.get("metadata", {}),
                "embedding_backend": "jina_late",
                "embedding_model": model_name,
            }
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add embeddings to chunks."""
    if active_chunking_method() == JINA_LATE_CHUNKING_METHOD:
        try:
            embedded = _embed_chunks_with_jina_late(chunks)
            if embedded is not None:
                return embedded
        except Exception:
            pass
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(EMBEDDING_MODEL)
        texts = [chunk["content"] for chunk in chunks]
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding.tolist()
            chunk["metadata"] = {
                **chunk.get("metadata", {}),
                "embedding_backend": "sentence_transformer",
                "embedding_model": EMBEDDING_MODEL,
            }
    except Exception:
        for chunk in chunks:
            chunk["embedding"] = hash_embedding(chunk["content"], EMBEDDING_DIM)
            chunk["metadata"] = {
                **chunk.get("metadata", {}),
                "embedding_backend": "hash",
                "embedding_model": "hash_embedding",
            }
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """Persist chunks to a local JSON vector store cache."""
    save_chunks(chunks)


def run_pipeline():
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {active_chunking_method()} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("Indexed to local vector store")


if __name__ == "__main__":
    run_pipeline()
