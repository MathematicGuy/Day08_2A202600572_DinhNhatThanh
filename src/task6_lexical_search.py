"""Task 6 - Lexical search.

Default search is BM25. A TF-IDF cosine option is included for the bonus demo:
TF-IDF gives high weight to terms that are frequent in one document but rare in
the corpus, then compares query/document vectors by cosine similarity.
"""

import math
from collections import Counter

from .local_index import ensure_chunks, metadata_matches, tokenize

CORPUS: list[dict] = []


def build_bm25_index(corpus: list[dict]):
    tokenized_corpus = [tokenize(doc["content"]) for doc in corpus]
    try:
        from rank_bm25 import BM25Okapi

        return BM25Okapi(tokenized_corpus)
    except Exception:
        return _SimpleBM25(tokenized_corpus)


class _SimpleBM25:
    def __init__(self, tokenized_corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.docs = tokenized_corpus
        self.k1 = k1
        self.b = b
        self.avgdl = sum(len(doc) for doc in tokenized_corpus) / max(1, len(tokenized_corpus))
        self.doc_freq = Counter()
        for doc in tokenized_corpus:
            self.doc_freq.update(set(doc))

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = []
        n_docs = max(1, len(self.docs))
        for doc in self.docs:
            counts = Counter(doc)
            doc_len = len(doc) or 1
            score = 0.0
            for token in query_tokens:
                if token not in counts:
                    continue
                idf = math.log(1 + (n_docs - self.doc_freq[token] + 0.5) / (self.doc_freq[token] + 0.5))
                tf = counts[token]
                denom = tf + self.k1 * (1 - self.b + self.b * doc_len / max(1, self.avgdl))
                score += idf * (tf * (self.k1 + 1)) / denom
            scores.append(score)
        return scores


def _load_corpus() -> list[dict]:
    global CORPUS
    if not CORPUS:
        CORPUS = [
            {"content": chunk["content"], "metadata": chunk.get("metadata", {})}
            for chunk in ensure_chunks()
        ]
    return CORPUS


def _tfidf_scores(query: str, corpus: list[dict]) -> list[float]:
    tokenized_docs = [tokenize(doc["content"]) for doc in corpus]
    query_counts = Counter(tokenize(query))
    n_docs = max(1, len(tokenized_docs))
    df = Counter()
    for doc in tokenized_docs:
        df.update(set(doc))

    def vector(counts: Counter) -> dict[str, float]:
        values = {}
        for token, tf in counts.items():
            idf = math.log((1 + n_docs) / (1 + df[token])) + 1
            values[token] = tf * idf
        return values

    query_vec = vector(query_counts)
    query_norm = math.sqrt(sum(v * v for v in query_vec.values())) or 1.0
    scores = []
    for doc_tokens in tokenized_docs:
        doc_vec = vector(Counter(doc_tokens))
        doc_norm = math.sqrt(sum(v * v for v in doc_vec.values())) or 1.0
        dot = sum(query_vec.get(token, 0.0) * doc_vec.get(token, 0.0) for token in query_vec)
        scores.append(dot / (query_norm * doc_norm))
    return scores


def lexical_search(
    query: str,
    top_k: int = 10,
    method: str = "bm25",
    filters: dict | None = None,
) -> list[dict]:
    if top_k <= 0:
        return []

    corpus = [doc for doc in _load_corpus() if metadata_matches(doc.get("metadata", {}), filters)]
    if not corpus:
        return []

    if method == "tfidf":
        scores = _tfidf_scores(query, corpus)
    else:
        bm25 = build_bm25_index(corpus)
        scores = bm25.get_scores(tokenize(query))

    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    results = []
    for idx, score in ranked[:top_k]:
        results.append(
            {
                "content": corpus[idx]["content"],
                "score": float(score),
                "metadata": corpus[idx].get("metadata", {}),
            }
        )
    return results


if __name__ == "__main__":
    for r in lexical_search("Dieu 249 tang tru trai phep chat ma tuy", top_k=5):
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
