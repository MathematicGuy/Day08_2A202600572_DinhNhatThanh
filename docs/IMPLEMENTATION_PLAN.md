# Implementation Plan

This plan reflects the current priority order agreed with the user. It is implementation-oriented, but no milestone should hardcode API keys or make PageIndex a default retrieval path.

## Priority Order

1. Optimization
2. RAGAS evaluation
3. Update RAG flow docs
4. Streamlit UI for RAGAS
5. Streamlit UI for evaluation/comparison
6. Airflow monitoring, Docker, and Wave/related infrastructure

PageIndex must remain the last-option fallback only. Do not use PageIndex by default, and do not include it in required test runs. Add comments/placeholders for later PageIndex work where useful.

## Milestone 1: Optimization

Goal: reduce end-to-end latency without losing answer quality, using a benchmark-first workflow.

### 1.1 Security Cleanup Before Benchmarks

- Remove sensitive-looking values from `.env.example` and committed tests.
- Keep real secrets only in `.env`.
- Update external-provider tests to read API keys from environment variables and skip when missing.
- Sanitize `tests/test_model.py` so it never contains hardcoded Jina, OpenAI, OpenRouter, Mistral, PageIndex, or other tokens.

### 1.2 Baseline Latency Benchmark

- Add a benchmark runner that uses `group_project/evaluation/golden_dataset.json` by default.
- Measure latency for each major stage:
  - query routing
  - query transformation
  - dense retrieval
  - lexical retrieval
  - fusion
  - reranking
  - fallback
  - context formatting
  - generation
  - self-correction
- Save benchmark output as JSON/CSV under `group_project/evaluation/` or `data/evaluation/`.
- Include per-query and aggregate metrics: average latency, p50, p95, max latency, retrieved source count, and whether fallback was used.

### 1.3 Task 9 Query Transformation Optimization

- Add configurable caps for query transformation:
  - maximum number of query variants
  - maximum query variant token/word length
  - maximum HyDE token/word length
  - option to disable LLM-generated variants
  - option to disable HyDE
- Keep current behavior as the baseline config.
- Add a faster config for comparison:
  - fewer query variants
  - shorter query variant length
  - no HyDE unless explicitly enabled
  - optional no-LLM query transformation
- Cache query transformation results per input query/config during a Streamlit session and benchmark run.

### 1.4 Retrieval and Reranking Optimization Candidates

- Benchmark current hybrid retrieval as baseline.
- Compare against:
  - lower `top_k` candidates before fusion/rerank
  - rerank on/off
  - RRF vs alpha fusion
  - dense-only and lexical-only diagnostic modes
  - local overlap reranker vs Jina reranker when `JINA_API_KEY` is provided
- Do not test PageIndex as a default comparison config. Leave it as a commented last fallback path only.

### 1.5 PDF Ingestion and Preprocessing Audit

- Inspect 1-2 standardized legal Markdown files against their source PDFs before finalizing retrieval latency changes.
- Default pilot documents:
  - `data/standardized/legal/luat-phong-chong-ma-tuy-2021.md`
  - `data/landing/legal/luat-phong-chong-ma-tuy-2021.pdf`
  - `data/standardized/legal/nghi-dinh-105-2021.md`
  - `data/landing/legal/nghi-dinh-105-2021.pdf`
- Document current extraction issues:
  - split Vietnamese words
  - awkward line breaks
  - page headers/footers mixed into body text
  - duplicated page furniture
  - noisy chunk boundaries
- Add a Mistral OCR pilot path using `mistralai` and `mistral-ocr-latest`.
- Compare baseline Markdown extraction vs Mistral OCR output for:
  - text cleanliness
  - structure preservation
  - downstream chunk quality
  - retrieval quality
  - processing latency/cost
- Store Mistral OCR output as a separate candidate corpus first; do not overwrite baseline standardized Markdown until comparison results justify it.

### 1.6 Acceptance Criteria

- A benchmark report exists for the baseline config.
- At least two optimized configs are benchmarked against baseline.
- Query transformation token/variant caps are configurable.
- Mistral OCR pilot results are available for the selected legal PDFs.
- PageIndex remains disabled as a normal benchmark/evaluation option.

## Milestone 2: RAGAS Evaluation

Goal: replace placeholder overlap metrics with a real RAGAS evaluation pipeline.

### 2.1 Dataset and Input Shape

- Use `group_project/evaluation/golden_dataset.json` as the source of truth.
- Convert each case into the RAGAS-compatible fields:
  - question/user input
  - generated answer/response
  - retrieved contexts
  - ground truth/expected answer
- Keep support for A/B comparison between pipeline configs.

### 2.2 Metrics

- Implement RAGAS metrics required by the group project:
  - faithfulness
  - answer/response relevancy
  - context precision
  - context recall
- Record latency alongside RAGAS scores for each case and config.

### 2.3 Config Comparison

- Baseline config: current RAG pipeline.
- Optimized config: best Milestone 1 latency config.
- Optional configs:
  - Mistral OCR corpus vs baseline corpus
  - local reranker vs Jina reranker
  - chunking variants
- PageIndex is not part of default RAGAS evaluation; keep it only as a later fallback note.

### 2.4 Outputs

- Save raw per-case results as JSON.
- Save summary tables as Markdown/CSV.
- Include worst performers with question, answer, contexts, metric scores, and likely failure reason.

### 2.5 Acceptance Criteria

- RAGAS evaluation runs on the golden dataset.
- Results include per-case metrics and aggregate metrics.
- Baseline and at least one optimized config are compared.
- Missing judge/model API keys produce clear skip/degradation behavior, not crashes.

## Milestone 3: Update RAG Flow Docs

Goal: keep architecture documentation aligned with the optimized and evaluated pipeline.

### 3.1 Update `docs/RAG_FLOW.md`

- Add the benchmark-first optimization flow.
- Add query transformation caps and caching.
- Add the PDF ingestion audit and Mistral OCR candidate preprocessing path.
- Add RAGAS evaluation flow and outputs.
- Add Streamlit RAGAS visualization and comparison pages.
- Keep PageIndex documented only as last-option fallback.

### 3.2 Update Requirements/Runbook Notes

- Keep `docs/USER_REQUIREMENTS.md` aligned with implemented secrets, inputs, and defaults.
- Add run commands for benchmark, RAGAS evaluation, and Streamlit multipage app.

### 3.3 Acceptance Criteria

- Docs match implemented files and behavior.
- PageIndex is described as optional last fallback, not a default dependency.

## Milestone 4: Streamlit UI for RAGAS

Goal: add a dedicated UI section/page to visualize the RAGAS evaluation process.

### 4.1 UI Placement

- Use Streamlit multipage app structure.
- Add a dedicated RAGAS visualization page or section under the Evaluation page.
- Keep chat functionality separate from evaluation workflows.

### 4.2 RAGAS Process Visualization

- Show selected dataset and selected pipeline config.
- Show run status and progress across evaluation cases.
- For each case, display:
  - question
  - generated answer
  - retrieved contexts
  - ground truth
  - faithfulness
  - answer/response relevancy
  - context precision
  - context recall
  - latency
  - pass/fail status
- Show aggregate score cards and worst-performing examples.
- Allow export/download of JSON/CSV/Markdown results.

### 4.3 Acceptance Criteria

- User can run or load RAGAS results from the UI.
- User can inspect individual cases and aggregate metrics.
- UI does not require restarting Streamlit to switch from chat to RAGAS visualization.

## Milestone 5: Streamlit UI for Evaluation and Comparison

Goal: let the user compare pipeline options visually and quickly.

### 5.1 Configurable Comparison Options

- Add controls for:
  - chunking method
  - chunk size and overlap
  - OCR source: baseline extraction vs Mistral OCR candidate output
  - reranker: local baseline vs Jina when configured
  - query transformation mode
  - fusion method
  - top_k
- Keep baseline config easy to restore.

### 5.2 Visualizations

- Show latency vs quality comparison.
- Show RAGAS metric deltas between configs.
- Show retrieved contexts side-by-side for selected questions.
- Show ingestion quality notes for OCR/preprocessing comparisons.

### 5.3 Acceptance Criteria

- User can compare at least baseline vs optimized config in Streamlit.
- User can inspect chunking/OCR/reranker choices and see their impact.
- Page switching works through Streamlit multipage navigation without restarting the app.

## Milestone 6: Airflow Monitoring, Docker, and Wave/Related Infrastructure

Goal: add orchestration and monitoring after the core optimization/evaluation/UI work is stable.

### 6.1 Airflow Local Docker

- Add Airflow Docker Compose setup.
- Add DAGs for:
  - legal document collection
  - news crawling
  - markdown conversion
  - indexing
  - benchmark/evaluation
- Use clear task logs and status for monitoring data processing.

### 6.2 Docker and Infrastructure Notes

- Add runbook for starting Airflow locally.
- Add environment variable guidance for Docker/Airflow.
- Keep secrets out of Docker Compose files unless using environment references.

### 6.3 Wave/Related Infrastructure

- Treat "Wave" as a later infrastructure item until clarified.
- If "Wave" means Weaviate, plan it as an optional vector-store experiment after Airflow is stable.
- Do not replace the current local JSON index by default.

### 6.4 Acceptance Criteria

- Airflow UI can monitor the data processing DAGs.
- Pipeline tasks can be rerun from Airflow.
- Docker setup is documented.
- Wave/Weaviate remains optional until clarified.

## Global Implementation Rules

- Do not hardcode API keys.
- Do not make PageIndex a default path.
- Do not require PageIndex for tests.
- Preserve the current working RAG pipeline as the baseline.
- Add new configs as optional comparison paths before changing defaults.
- Prefer measurable latency and RAGAS evidence before adopting an optimization.
