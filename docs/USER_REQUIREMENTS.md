# User Requirements Before Implementation

This file lists the user-provided inputs needed before implementing the latency optimization, Airflow monitoring, RAGAS evaluation, documentation update, and Streamlit comparison UI plan.

## Confirmed Choices

- Latency strategy: benchmark-first.
- Airflow setup: local Docker Compose.
- Streamlit evaluation UI: multipage app using `pages/`.
- Documentation target: update `docs/RAG_FLOW.md`.

## Required Secrets and `.env` Values

Do not commit real secrets. Put them in `.env` only, and keep `.env.example` as placeholders.

Required for LLM generation and RAGAS judge/model calls:

- `OPENROUTER_API_KEY` or `OPENAI_API_KEY`
- `OPENROUTER_BASE_URL`, if using OpenRouter or another OpenAI-compatible provider
- `OPENROUTER_MODEL`, for example the model currently used by generation
- RAGAS judge model/provider preference, if different from the existing OpenRouter/OpenAI-compatible setup
- Confirm whether RAGAS visualization should run inside the Streamlit Evaluation page. Default: yes, as a dedicated RAGAS visualization section/page in the multipage app.

Required for Jina reranker comparisons:

- `JINA_API_KEY`
- Preferred Jina reranker model. Default if not specified: `jinaai/jina-reranker-v2-base-multilingual` when using local/model naming, or the closest supported Jina API rerank model if using hosted API.

Required for Mistral OCR comparisons:

- `MISTRAL_API_KEY`
- Preferred OCR mode:
  - direct OCR for small local experiments
  - batch OCR for larger PDF/image batches
- OCR model. Default if not specified: `mistral-ocr-latest`.

Optional for PageIndex fallback:

- `PAGEINDEX_API_KEY`
- `PAGEINDEX_INDEX_ID`
- `PAGEINDEX_API_URL`

Required for Airflow local Docker:

- Docker Desktop or Docker Engine available on the machine.
- Permission to add Airflow files such as `docker-compose.airflow.yml`, `airflow/dags/`, `airflow/logs/`, and `airflow/plugins/`.
- Optional `AIRFLOW_UID` value for Linux/WSL file ownership. If not provided, use the standard local setup default from Airflow Docker docs.

## URLs and External References

User-provided or approved references:

- Mistral OCR batch cookbook: `https://docs.mistral.ai/resources/cookbooks/mistral-ocr-batch_ocr`
- Jina reranker target: `jinaai/jina-reranker-v2-base-multilingual`
- Existing group project evaluation requirements: `group_project/README.md`
- Existing model test reference: `tests/test_model.py`

Implementation will use official/current docs for:

- Mistral OCR and Batch API workflow.
- RAGAS metrics and evaluation APIs.
- Apache Airflow Docker Compose and TaskFlow DAG patterns.

## Data and Evaluation Inputs Needed

Golden dataset:

- Confirm whether `group_project/evaluation/golden_dataset.json` is the evaluation source of truth.
- If it is incomplete, provide additional question/answer/context cases or approve generating more cases from existing documents.
- Confirm which RAGAS process details should be visible in the UI. Default: per-question answer, retrieved contexts, ground truth, faithfulness, answer/response relevancy, context precision, context recall, average score, latency, pass/fail status, and worst-performing examples.

Latency benchmark queries:

- Provide 10-30 representative user questions for latency measurement, or approve using questions from `golden_dataset.json`.
- Confirm whether benchmark results should optimize for average latency, p95 latency, RAGAS score retention, or a weighted score.

PDF ingestion/preprocessing audit:

- Inspect 1-2 standardized legal Markdown files against their matching source files in `data/landing/legal/` before optimizing retrieval latency.
- Default inspection sample:
  - `data/standardized/legal/luat-phong-chong-ma-tuy-2021.md` vs `data/landing/legal/luat-phong-chong-ma-tuy-2021.pdf`
  - `data/standardized/legal/nghi-dinh-105-2021.md` vs `data/landing/legal/nghi-dinh-105-2021.pdf`
- Current previewed issues include split Vietnamese words, awkward line breaks, page headers/footers mixed into body text, duplicated page furniture, and likely noisy chunk boundaries.
- Compare baseline PDF extraction against Mistral OCR output before deciding whether OCR should replace or supplement current preprocessing.
- Track OCR comparison as a Milestone 1 latency/quality task because better Markdown can reduce noisy chunks, improve retrieval relevance, and reduce downstream reranking/generation work.

OCR comparison corpus:

- Provide which PDFs/images should be used for OCR comparison.
- Confirm whether OCR output should replace current standardized Markdown or be stored as a separate candidate output for comparison.
- If no corpus is provided, use the two legal documents listed in the PDF ingestion/preprocessing audit as the OCR pilot set.
- Use Mistral Document AI OCR via `mistralai` and `mistral-ocr-latest` by default.
- Capture OCR metadata where available, including page-level Markdown, tables, headers/footers, and confidence scores.

Chunking comparison:

- Confirm the chunking methods to compare. Default set:
  - recursive character splitter
  - markdown header splitter where headings exist
  - fixed character fallback
- Confirm chunk sizes and overlaps to test, or approve a small grid around the current `500/50` baseline.

Reranker comparison:

- Confirm whether Jina reranking should be hosted API only, local model only, or both.
- Confirm whether the current local overlap reranker remains the baseline.

## Security Cleanup Required Before Proceeding

The repository currently contains sensitive-looking values in files that should not contain real keys. Before implementation, rotate any exposed keys and replace committed examples with placeholders.

Files to inspect and sanitize:

- `.env.example`
- `tests/test_model.py`
- Any committed notebook, test, or docs file that includes API tokens

Implementation should never hardcode API keys. Tests should read secrets from `.env` or skip external-provider tests when keys are missing.

## Defaults If No Further Input Is Provided

- Use `golden_dataset.json` as the benchmark and RAGAS dataset.
- Optimize by measured latency while requiring no major regression in RAGAS average score.
- Add token and variant caps to Task 9 query transformation, controlled by environment variables.
- Add a Milestone 1 PDF ingestion/preprocessing audit comparing current legal Markdown against source PDFs, then benchmark Mistral OCR output as an alternative preprocessing path.
- Keep current retrieval behavior as the baseline config.
- Add optional configs for chunking, OCR, and reranking without replacing the baseline.
- Store benchmark/evaluation outputs under `group_project/evaluation/` or `data/evaluation/`.
- Use Streamlit multipage navigation:
  - Chat page
  - Evaluation and comparison page
- Add a dedicated RAGAS visualization UI in the Evaluation page so users can watch the evaluation process, inspect per-case metrics, compare configs, and export results.
- Use Airflow DAGs to monitor data collection, conversion, indexing, and evaluation jobs.
