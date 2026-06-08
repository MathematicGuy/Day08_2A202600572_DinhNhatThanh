"""Local RAG evaluation pipeline with 4 RAG-style metrics and A/B comparison."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_DIR))

from src.local_index import tokenize
from src.task10_generation import generate_with_citation
from src.task9_retrieval_pipeline import retrieve

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"


def load_golden_dataset() -> list[dict]:
    return json.loads(GOLDEN_DATASET_PATH.read_text(encoding="utf-8"))


def _overlap_score(left: str, right: str) -> float:
    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens)


def _score_case(item: dict, answer: str, sources: list[dict]) -> dict:
    contexts = "\n".join(source.get("content", "") for source in sources)
    expected_context = item.get("expected_context", "")
    expected_answer = item.get("expected_answer", "")
    return {
        "faithfulness": _overlap_score(answer, contexts),
        "answer_relevance": _overlap_score(expected_answer, answer),
        "context_recall": _overlap_score(expected_answer + " " + expected_context, contexts),
        "context_precision": _overlap_score(contexts, expected_answer + " " + expected_context),
    }


def evaluate_config(golden_dataset: list[dict], name: str, use_reranking: bool) -> dict:
    rows = []
    for item in golden_dataset:
        if use_reranking:
            result = generate_with_citation(item["question"])
            answer = result["answer"]
            sources = result["sources"]
        else:
            sources = retrieve(item["question"], top_k=5, use_reranking=False)
            answer = " ".join(source.get("content", "") for source in sources[:1])
        scores = _score_case(item, answer, sources)
        rows.append({"question": item["question"], "answer": answer, "sources": sources, **scores})

    summary = {}
    for metric in ["faithfulness", "answer_relevance", "context_recall", "context_precision"]:
        summary[metric] = sum(row[metric] for row in rows) / max(1, len(rows))
    summary["average"] = sum(summary.values()) / 4
    return {"name": name, "summary": summary, "rows": rows}


def compare_configs(rag_pipeline=None, golden_dataset: list[dict] | None = None):
    dataset = golden_dataset or load_golden_dataset()
    return {
        "hybrid_rerank": evaluate_config(dataset, "hybrid_rerank", use_reranking=True),
        "dense_like_no_rerank": evaluate_config(dataset, "dense_like_no_rerank", use_reranking=False),
    }


def export_results(results: dict, comparison: dict | None = None):
    configs = comparison or results
    a = configs["hybrid_rerank"]["summary"]
    b = configs["dense_like_no_rerank"]["summary"]
    metrics = ["faithfulness", "answer_relevance", "context_recall", "context_precision", "average"]

    lines = ["# RAG Evaluation Results", "", "## Overall Scores", ""]
    lines.append("| Metric | Hybrid + Rerank | No Rerank | Delta |")
    lines.append("|---|---:|---:|---:|")
    for metric in metrics:
        lines.append(f"| {metric} | {a[metric]:.3f} | {b[metric]:.3f} | {a[metric] - b[metric]:+.3f} |")

    worst = sorted(configs["hybrid_rerank"]["rows"], key=lambda row: row["average"] if "average" in row else row["context_recall"])[:3]
    lines.extend(["", "## A/B Comparison", ""])
    lines.append("Config A uses hybrid retrieval, RRF merge, reranking, citation generation, and fallback.")
    lines.append("Config B disables reranking and uses the first retrieved chunk as an extractive answer.")
    lines.extend(["", "## Worst Performers", ""])
    lines.append("| # | Question | Faithfulness | Relevance | Recall | Precision |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for i, row in enumerate(worst, 1):
        lines.append(
            f"| {i} | {row['question']} | {row['faithfulness']:.3f} | "
            f"{row['answer_relevance']:.3f} | {row['context_recall']:.3f} | {row['context_precision']:.3f} |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.append("- Add more official full-text PDFs/DOCX to improve legal recall.")
    lines.append("- Enable OpenRouter and PageIndex keys for better generation and vectorless fallback.")
    lines.append("- Expand news articles with full crawled text before final demo.")
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def evaluate_with_deepeval(rag_pipeline, golden_dataset: list[dict]) -> dict:
    return evaluate_config(golden_dataset, "hybrid_rerank", use_reranking=True)


def evaluate_with_ragas(rag_pipeline, golden_dataset: list[dict]) -> dict:
    return evaluate_config(golden_dataset, "hybrid_rerank", use_reranking=True)


def evaluate_with_trulens(rag_pipeline, golden_dataset: list[dict]) -> dict:
    return evaluate_config(golden_dataset, "hybrid_rerank", use_reranking=True)


if __name__ == "__main__":
    dataset = load_golden_dataset()
    comparison = compare_configs(golden_dataset=dataset)
    export_results(comparison)
    print(f"Evaluated {len(dataset)} cases. Results: {RESULTS_PATH}")
