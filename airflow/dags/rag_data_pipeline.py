"""Airflow DAG for monitoring the local RAG data-processing pipeline.

PageIndex is intentionally not part of this default DAG. Keep it as a later
last-option fallback only when explicitly enabled.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task

PROJECT_DIR = Path("/opt/airflow/project")


def _run(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout[-4000:]


@dag(
    dag_id="rag_data_processing_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["rag", "data-processing", "monitoring"],
)
def rag_data_processing_pipeline():
    @task
    def collect_legal_docs():
        return _run(["python", "-m", "src.task1_collect_legal_docs"])

    @task
    def crawl_news():
        return _run(["python", "-m", "src.task2_crawl_news"])

    @task
    def convert_markdown():
        return _run(["python", "-m", "src.task3_convert_markdown"])

    @task
    def build_index():
        return _run(["python", "-m", "src.task4_chunking_indexing"])

    @task
    def latency_benchmark():
        return _run(["python", "-m", "src.benchmark_latency"])

    [collect_legal_docs(), crawl_news()] >> convert_markdown() >> build_index() >> latency_benchmark()


rag_data_processing_pipeline()
