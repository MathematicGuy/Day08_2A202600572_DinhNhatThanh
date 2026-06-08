"""Task 4 - Chunking and local indexing."""

from pathlib import Path

from .local_index import hash_embedding, read_markdown_documents, save_chunks

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Recursive chunking is robust for mixed legal markdown and news articles.
# 500 chars keeps chunks focused; 50 chars overlap preserves citation context.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

# This lightweight model is easy to run locally. If sentence-transformers or
# weights are unavailable, embed_chunks falls back to deterministic hashing.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
VECTOR_STORE = "local-json"


def load_documents() -> list[dict]:
    """Read markdown files from data/standardized/."""
    return read_markdown_documents()


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
                        "metadata": {**doc["metadata"], "chunk_index": i},
                    }
                )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add embeddings to chunks."""
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(EMBEDDING_MODEL)
        texts = [chunk["content"] for chunk in chunks]
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding.tolist()
    except Exception:
        for chunk in chunks:
            chunk["embedding"] = hash_embedding(chunk["content"], EMBEDDING_DIM)
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """Persist chunks to a local JSON vector store cache."""
    save_chunks(chunks)


def run_pipeline():
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
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
