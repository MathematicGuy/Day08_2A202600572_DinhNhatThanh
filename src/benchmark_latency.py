"""Latency benchmark helpers for RAG configs."""

from __future__ import annotations

import csv
import json
import os
import statistics
import time
from contextlib import contextmanager
from pathlib import Path

from .task10_generation import generate_with_citation

PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_DATASET = PROJECT_DIR / "group_project" / "evaluation" / "golden_dataset.json"
OUTPUT_DIR = PROJECT_DIR / "group_project" / "evaluation"


BASELINE_CONFIG = {
    "name": "baseline",
    "env": {
        "RAG_QUERY_MAX_VARIANTS": "3",
        "RAG_QUERY_MAX_WORDS": "48",
        "RAG_HYDE_MAX_WORDS": "120",
        "RAG_DISABLE_LLM_QUERY_VARIANTS": "0",
        "HYDE_ENABLED": "0",
        "PAGEINDEX_FALLBACK_ENABLED": "0",
    },
}

FAST_CONFIG = {
    "name": "fast_no_llm_transform",
    "env": {
        "RAG_QUERY_MAX_VARIANTS": "1",
        "RAG_QUERY_MAX_WORDS": "32",
        "RAG_HYDE_MAX_WORDS": "0",
        "RAG_DISABLE_LLM_QUERY_VARIANTS": "1",
        "HYDE_ENABLED": "0",
        "PAGEINDEX_FALLBACK_ENABLED": "0",
    },
}

SHORT_MULTI_QUERY_CONFIG = {
    "name": "short_multi_query",
    "env": {
        "RAG_QUERY_MAX_VARIANTS": "2",
        "RAG_QUERY_MAX_WORDS": "36",
        "RAG_HYDE_MAX_WORDS": "80",
        "RAG_DISABLE_LLM_QUERY_VARIANTS": "0",
        "HYDE_ENABLED": "0",
        "PAGEINDEX_FALLBACK_ENABLED": "0",
    },
}


@contextmanager
def temporary_env(overrides: dict[str, str]):
    old_values = {key: os.getenv(key) for key in overrides}
    try:
        for key, value in overrides.items():
            os.environ[key] = value
        yield
    finally:
        for key, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def load_questions(dataset_path: Path = DEFAULT_DATASET, limit: int | None = None) -> list[str]:
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    questions = [item["question"] for item in data if item.get("question")]
    return questions[:limit] if limit else questions


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def summarize_rows(rows: list[dict]) -> dict:
    latencies = [float(row["total_latency_ms"]) for row in rows]
    return {
        "count": len(rows),
        "avg_latency_ms": statistics.mean(latencies) if latencies else 0.0,
        "p50_latency_ms": statistics.median(latencies) if latencies else 0.0,
        "p95_latency_ms": _percentile(latencies, 0.95),
        "max_latency_ms": max(latencies) if latencies else 0.0,
        "fallback_count": sum(1 for row in rows if row.get("retrieval_source") == "pageindex"),
    }


def run_latency_benchmark(
    configs: list[dict] | None = None,
    dataset_path: Path = DEFAULT_DATASET,
    limit: int | None = None,
    top_k: int = 5,
) -> dict:
    questions = load_questions(dataset_path, limit=limit)
    configs = configs or [BASELINE_CONFIG, FAST_CONFIG, SHORT_MULTI_QUERY_CONFIG]
    results = {"dataset": str(dataset_path), "configs": []}

    for config in configs:
        rows = []
        with temporary_env(config.get("env", {})):
            for question in questions:
                started = time.perf_counter()
                result = generate_with_citation(question, top_k=top_k)
                elapsed_ms = (time.perf_counter() - started) * 1000
                timings = result.get("timings", {})
                rows.append(
                    {
                        "config": config["name"],
                        "question": question,
                        "answer": result.get("answer", ""),
                        "source_count": len(result.get("sources", [])),
                        "retrieval_source": result.get("retrieval_source", "none"),
                        "total_latency_ms": elapsed_ms,
                        **{f"timing_{key}": value for key, value in timings.items()},
                    }
                )
        results["configs"].append({"name": config["name"], "env": config.get("env", {}), "summary": summarize_rows(rows), "rows": rows})

    return results


def export_latency_results(results: dict, output_dir: Path = OUTPUT_DIR) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "latency_benchmark_results.json"
    csv_path = output_dir / "latency_benchmark_results.csv"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = [row for config in results.get("configs", []) for row in config.get("rows", [])]
    if rows:
        fieldnames = sorted({key for row in rows for key in row})
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return {"json": json_path, "csv": csv_path}


if __name__ == "__main__":
    try:
        benchmark_limit = int(os.getenv("BENCHMARK_LIMIT", "5"))
    except ValueError:
        benchmark_limit = 5
    output = run_latency_benchmark(limit=benchmark_limit)
    paths = export_latency_results(output)
    print(f"Latency benchmark saved: {paths['json']}")
