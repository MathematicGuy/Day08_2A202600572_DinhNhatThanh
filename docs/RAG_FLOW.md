# RAG Flow

This document maps the implemented RAG pipeline from data collection to answer generation. It reflects the current code paths in `src/`, `app.py`, and the local data layout.

## End-to-End Flow

```text
Legal document URLs + news article URLs
        |
        v
Task 1/2: Data collection
        |
        +-- legal PDFs/DOC files -> data/landing/legal/
        +-- news JSON files      -> data/landing/news/
        |
        v
Task 3: Standardization to Markdown
        |
        +-- data/standardized/legal/*.md
        +-- data/standardized/news/*.md
        |
        v
Task 4: Chunking and indexing
        |
        +-- recursive chunks, size=500, overlap=50
        +-- embeddings: sentence-transformers/all-MiniLM-L6-v2 or hash fallback
        +-- local JSON vector store: data/index/chunks.json
        |
        v
User query from Streamlit
        |
        v
Task 9: Query router
        |
        +-- prompt-injection guardrail
        +-- out-of-scope guardrail
        +-- legal/news/criminal-law routing and metadata filters
        |
        v
Task 9: Query transformation
        |
        +-- multi-query variants
        +-- synonym expansion
        +-- optional HyDE when HYDE_ENABLED=1 and OpenRouter is configured
        |
        v
Hybrid retrieval per query variant
        |
        +-- dense:   semantic_search()
        +-- lexical: lexical_search() with BM25 by default
        |
        v
Fusion and reranking
        |
        +-- RRF by default, or alpha fusion when FUSION_METHOD=alpha
        +-- local cross-encoder-style rerank by default
        |
        v
Optional last fallback when hybrid is empty or below score threshold
        |
        +-- disabled by default with PAGEINDEX_FALLBACK_ENABLED=0
        +-- PageIndex/local vectorless only when explicitly enabled
        |
        v
Task 10: Context formatting and generation
        |
        +-- reorder chunks for LLM
        +-- format sources for citation
        +-- OpenRouter/OpenAI-compatible generation when configured
        +-- extractive fallback when no API key or LLM failure
        |
        v
Task 10: Self-correction
        |
        +-- citation check
        +-- context-support check
        +-- LLM correction or extractive fallback
        |
        v
Streamlit response
        |
        +-- answer
        +-- safe thought-process summary
        +-- degradation events
        +-- source documents, scores, metadata, snippets
```

## Data Collection

Legal documents are collected by `src/task1_collect_legal_docs.py`.

- Source pages are listed in `LEGAL_DOCS`.
- The downloader resolves PDF/DOC links from Cong Bao pages, including multi-part downloads when `download_all` is set.
- Files are saved into `data/landing/legal/`.
- `setup_directory()` recreates the legal landing set by deleting previous `*.pdf` files before download.

News articles are collected by `src/task2_crawl_news.py`.

- Article URLs are listed in `ARTICLE_URLS`.
- Each page is fetched with `requests`, then title and article body are extracted from HTML.
- Each saved JSON contains `url`, `title`, `date_crawled`, and `content_markdown`.
- Files are saved as `data/landing/news/article_XX.json`.

## Standardization

`src/task3_convert_markdown.py` converts landing files into Markdown under `data/standardized/`.

- Legal files from `data/landing/legal/` are converted into `data/standardized/legal/*.md`.
- News JSON files from `data/landing/news/` are converted into `data/standardized/news/*.md`.
- News Markdown prepends source metadata: title, original URL, crawl time, then article content.
- PDF extraction tries `pypdf` first. If that does not produce clean text, it tries `markitdown`. If the file is text-like, it falls back to reading text directly.
- Binary-looking extraction output is rejected to avoid indexing corrupted text.

## Chunking and Indexing

`src/task4_chunking_indexing.py` builds the local retrieval index.

- Markdown is loaded through `read_markdown_documents()` in `src/local_index.py`.
- Each document receives metadata:
  - `source`
  - `source_label`
  - `path`
  - `type` as `legal` or `news`
  - `year` when detected from filename or document text
- Chunking uses `RecursiveCharacterTextSplitter` when available.
- Chunking settings are:
  - `CHUNKING_METHOD = "recursive"`
  - `CHUNK_SIZE = 500`
  - `CHUNK_OVERLAP = 50`
- If `langchain-text-splitters` is unavailable, the code falls back to fixed character windows using the same size and overlap.
- Embeddings use `sentence-transformers/all-MiniLM-L6-v2` with `EMBEDDING_DIM = 384`.
- If `sentence-transformers` or model weights are unavailable, chunks use deterministic hashing embeddings from `hash_embedding()`.
- `index_to_vectorstore()` persists chunks to `data/index/chunks.json` using `save_chunks()`.

The index file may not exist immediately after checkout. Query-time calls use `ensure_chunks()` from `src/local_index.py`, which loads `data/index/chunks.json` if present or lazily rebuilds chunks and embeddings from `data/standardized/` if the index is missing.

## Retrieval

`src/task9_retrieval_pipeline.py` orchestrates query-time retrieval.

### Routing

`rag_tool_router()` applies rule-based routing before retrieval.

- Prompt-injection-like queries are blocked and do not access RAG data.
- Out-of-scope queries are blocked and do not access RAG data.
- Legal questions receive `{"type": "legal"}` filters.
- News questions receive `{"type": "news"}` filters.
- Criminal-law questions receive `{"type": "legal", "path_contains": "hinh-su"}` filters.
- Mixed legal/news questions search both collections without a metadata filter.

The router also chooses whether to use multi-query, query expansion, optional HyDE, RRF/alpha fusion, and alpha weight.

### Query Transformation

`transform_query()` prepares search variants.

- Multi-query variants come from OpenRouter when configured.
- If LLM variants are unavailable, `_fallback_multi_query()` creates deterministic variants.
- `_expand_query()` appends Vietnamese synonyms and related terms for drug-law concepts.
- HyDE is added only when `HYDE_ENABLED=1` and an OpenRouter-compatible client is available.
- Milestone 1 latency controls cap query transformation:
  - `RAG_QUERY_MAX_VARIANTS`
  - `RAG_QUERY_MAX_WORDS`
  - `RAG_HYDE_MAX_WORDS`
  - `RAG_DISABLE_LLM_QUERY_VARIANTS`
- Query transformation results are cached per query/config during the Python process to avoid repeated LLM variant calls.

### Dense Retrieval

`semantic_search()` in `src/task5_semantic_search.py` performs vector search over local chunks.

- Query embeddings use `sentence-transformers/all-MiniLM-L6-v2` when available.
- If model loading fails, the query uses the same deterministic hash embedding fallback as indexing.
- Scores are cosine similarities.
- Optional metadata filters are applied before scoring.

### Lexical Retrieval

`lexical_search()` in `src/task6_lexical_search.py` performs sparse search.

- Default method is BM25.
- `rank_bm25.BM25Okapi` is used when installed.
- `_SimpleBM25` is used as a local fallback.
- `method="tfidf"` is available as a bonus alternative using TF-IDF cosine similarity.
- Optional metadata filters are applied before ranking.

### Fusion, Reranking, and Fallback

For each transformed query variant, retrieval runs dense and lexical search with `top_k * 2`, then fuses the results.

- Default fusion is reciprocal rank fusion through `rerank_rrf()`.
- `FUSION_METHOD=alpha` enables normalized weighted fusion through `_alpha_fusion()`.
- `FUSION_ALPHA` controls dense-vs-sparse weighting when alpha fusion is used.
- Multi-query result lists are merged again with RRF.
- Final reranking uses `rerank()` with `RERANK_METHOD = "cross_encoder"` by default.

The default reranker is local and lightweight. It combines query-token overlap with the incoming score. `task7_reranking.py` also includes MMR and RRF helpers.

If final hybrid results are empty or the best score is below `SCORE_THRESHOLD = 0.3`, retrieval can fall back to `pageindex_search()` only when explicitly enabled.

- `PAGEINDEX_FALLBACK_ENABLED=0` by default.
- If `PAGEINDEX_FALLBACK_ENABLED=1`, `PAGEINDEX_API_KEY`, and `PAGEINDEX_INDEX_ID` are configured, PageIndex API search is attempted.
- If PageIndex is unavailable or returns no usable result, local vectorless search scores chunks by token overlap.
- Fallback results are marked with `source = "pageindex"`.
- PageIndex is intentionally the last-option fallback and is not part of default benchmark or RAGAS evaluation configs.

Each retrieved result carries metadata for downstream display, including retrieval method, query variant, fusion method, applied metadata filter, query plan, query transform, and degradation events.

## Latency and Preprocessing Optimization

Milestone 1 adds benchmark-first optimization.

- `src/benchmark_latency.py` runs baseline and optimized configs over `group_project/evaluation/golden_dataset.json`.
- The benchmark records per-query latency and stage timings from retrieval and generation.
- Default comparison configs include:
  - baseline current behavior
  - fast no-LLM query transformation
  - shorter multi-query transformation
- Results are exported to `group_project/evaluation/latency_benchmark_results.json` and `.csv`.

The preprocessing audit compares current PDF extraction against Mistral OCR output.

- Current baseline Markdown can contain split Vietnamese words, awkward line breaks, page headers/footers in body text, and noisy chunk boundaries.
- `src/mistral_ocr.py` runs an OCR pilot with `mistral-ocr-latest` when `MISTRAL_API_KEY` is configured.
- OCR output is saved separately under `data/ocr/mistral/legal/`; it does not overwrite `data/standardized/` by default.
- Mistral OCR remains a candidate preprocessing path until latency/RAGAS results justify replacing the baseline extraction.

## RAGAS Evaluation

`group_project/evaluation/eval_pipeline.py` is RAGAS-first with local fallback metrics.

- The golden dataset comes from `group_project/evaluation/golden_dataset.json`.
- Each case is converted into question, generated answer, retrieved contexts, and ground truth.
- Target metrics are faithfulness, answer/response relevancy, context precision, and context recall.
- Latency is recorded alongside RAGAS scores.
- If RAGAS or judge credentials are unavailable, the script reports local overlap fallback metrics instead of crashing.
- Default configs compare baseline vs optimized-fast retrieval/generation behavior.
- PageIndex is not part of default RAGAS evaluation.

## Generation

`src/task10_generation.py` converts retrieved chunks into a cited Vietnamese answer.

`generate_with_citation()` is the main entrypoint.

- It calls `rag_tool_router()` first, so prompt-injection and out-of-scope queries can return direct safe responses without retrieval.
- For valid in-scope queries, it calls `retrieve()`.
- `reorder_for_llm()` keeps the strongest chunk first and moves the second strongest chunk near the end to reduce lost-in-the-middle effects.
- `format_context()` formats each chunk with source label, document type, score, and chunk index.
- The system prompt requires the model to answer only from context and cite factual claims with friendly source labels.

Generation uses `_openrouter_client()`.

- `OPENROUTER_API_KEY` is preferred.
- `OPENAI_API_KEY` is accepted as a fallback API key.
- `OPENROUTER_BASE_URL` defaults to `https://openrouter.ai/api/v1`.
- `OPENROUTER_MODEL` defaults to `openai/gpt-4o-mini`.
- Temperature is `0.3`; `top_p` is `0.9`.

If no API key is available or LLM generation fails, `_fallback_answer()` returns an extractive answer from the best retrieved chunk with citation. If no chunks exist, it returns a short unverifiable-answer message.

### Self-Correction

`self_correct_answer()` validates the generated answer.

- `_has_citation()` checks for bracketed citations.
- `_support_score()` compares answer tokens against retrieved context tokens.
- Answers with citations and support score at least `0.25` are accepted.
- If an LLM client is available and context exists, the code asks the model to repair unsupported or uncited answers.
- If repair fails, the code falls back to an extractive cited answer.

`_safe_thought_process()` returns a safe, user-facing summary of routing, query transformation, fusion, degradation, sources, and self-check status. It does not expose raw chain-of-thought.

## UI and Output

`app.py` provides the Streamlit chat interface.

- The UI calls `generate_with_citation(query)`.
- Chat messages are stored in `st.session_state.messages`.
- The assistant response displays:
  - final answer
  - safe thought-process summary
  - optional graceful-degradation details
  - source documents
  - source metadata
  - scores, retrieval method, fusion method
  - highlighted snippets based on the user query

If `generate_with_citation()` raises an exception, `app.py` catches it and returns a graceful app-level error response with a degradation event.

Streamlit multipage evaluation pages are also available.

- `pages/1_RAGAS_Evaluation.py` visualizes RAGAS evaluation process, per-case metrics, aggregate metrics, worst performers, retrieved contexts, and JSON export.
- `pages/2_Evaluation_Comparison.py` supports latency benchmarks, OCR preprocessing diagnostics, and config-comparison notes.
- Page switching uses Streamlit multipage navigation; the chat page stays separate from evaluation workflows.

## Public Interfaces

The main public functions exposed by the task modules are:

- `collect_legal_docs() -> list[Path]`
- `crawl_all()`
- `convert_all()`
- `run_pipeline()`
- `semantic_search(query, top_k=10, filters=None) -> list[dict]`
- `lexical_search(query, top_k=10, method="bm25", filters=None) -> list[dict]`
- `rerank(query, candidates, top_k=5, method="cross_encoder") -> list[dict]`
- `pageindex_search(query, top_k=5, filters=None) -> list[dict]`
- `retrieve(query, top_k=5, score_threshold=0.3, use_reranking=True, filters=None, fusion_method="rrf", alpha=0.5, transformations="auto") -> list[dict]`
- `generate_with_citation(query, top_k=5) -> dict`

## Environment Variables

Important optional configuration comes from `.env` or the shell environment.

- `OPENROUTER_API_KEY`: enables LLM query variants, HyDE, generation, and correction.
- `OPENAI_API_KEY`: accepted by generation as a fallback API key.
- `OPENROUTER_BASE_URL`: OpenAI-compatible base URL, defaulting to OpenRouter.
- `OPENROUTER_MODEL`: model name, defaulting to `openai/gpt-4o-mini`.
- `HYDE_ENABLED`: set to `1` to enable HyDE query expansion.
- `FUSION_METHOD`: `rrf` by default; set to `alpha` for weighted dense/sparse fusion.
- `FUSION_ALPHA`: dense weight for alpha fusion, default `0.5`.
- `PAGEINDEX_API_KEY`, `PAGEINDEX_INDEX_ID`, `PAGEINDEX_API_URL`: enable PageIndex vectorless retrieval.
- `PAGEINDEX_FALLBACK_ENABLED`: defaults to `0`; set to `1` only when intentionally testing the last-option fallback.
- `RAG_QUERY_MAX_VARIANTS`, `RAG_QUERY_MAX_WORDS`, `RAG_HYDE_MAX_WORDS`, `RAG_DISABLE_LLM_QUERY_VARIANTS`: latency controls for query transformation.
- `JINA_API_KEY`, `JINA_RERANKER_MODEL`, `RERANK_METHOD=jina`: optional Jina reranker comparison.
- `MISTRAL_API_KEY`, `MISTRAL_OCR_MODEL`: optional Mistral OCR preprocessing pilot.

## Runbook

```bash
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown
python -m src.task4_chunking_indexing
python -m src.benchmark_latency
python group_project/evaluation/eval_pipeline.py
python -m pytest tests/test_individual.py -v
streamlit run app.py
```

`src.task4_chunking_indexing` materializes `data/index/chunks.json`. If that file is missing, query-time retrieval can still lazily rebuild the local index from standardized Markdown through `ensure_chunks()`.

Airflow monitoring is scaffolded for later use:

```bash
docker compose -f docker-compose.airflow.yml up airflow-init
docker compose -f docker-compose.airflow.yml up airflow-webserver airflow-scheduler
```

Airflow UI runs on `http://localhost:8080` with local demo credentials `admin` / `admin`.
