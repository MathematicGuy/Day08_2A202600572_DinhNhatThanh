"""Streamlit page for latency, OCR, and retrieval configuration comparisons."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.benchmark_latency import (  # noqa: E402
    BASELINE_CONFIG,
    FAST_CONFIG,
    SHORT_MULTI_QUERY_CONFIG,
    export_latency_results,
    run_latency_benchmark,
)
from src.mistral_ocr import DEFAULT_PILOT_FILES, inspect_markdown_quality, run_pilot  # noqa: E402

st.set_page_config(page_title="RAG Pipeline Comparison", layout="wide")
st.title("Pipeline Evaluation and Comparison")

tab_latency, tab_ocr, tab_config = st.tabs(["Latency", "OCR preprocessing", "Config notes"])

with tab_latency:
    st.subheader("Latency benchmark")
    limit = st.slider("Số câu hỏi benchmark", min_value=1, max_value=15, value=5)
    selected = st.multiselect(
        "Configs",
        ["baseline", "fast_no_llm_transform", "short_multi_query"],
        default=["baseline", "fast_no_llm_transform"],
    )
    config_map = {
        "baseline": BASELINE_CONFIG,
        "fast_no_llm_transform": FAST_CONFIG,
        "short_multi_query": SHORT_MULTI_QUERY_CONFIG,
    }
    if st.button("Chạy latency benchmark", type="primary"):
        configs = [config_map[name] for name in selected]
        with st.status("Đang benchmark...", expanded=True) as status:
            results = run_latency_benchmark(configs=configs, limit=limit)
            paths = export_latency_results(results)
            status.update(label=f"Benchmark hoàn tất: {paths['json']}", state="complete")
        st.session_state["latency_results"] = results

    results = st.session_state.get("latency_results")
    if results:
        st.markdown("**Summary**")
        st.dataframe(
            [
                {"config": item["name"], **item.get("summary", {})}
                for item in results.get("configs", [])
            ],
            use_container_width=True,
        )
        selected_config = st.selectbox("Xem chi tiết config", [item["name"] for item in results.get("configs", [])])
        rows = next((item["rows"] for item in results.get("configs", []) if item["name"] == selected_config), [])
        st.dataframe(rows, use_container_width=True)
        st.download_button(
            "Download latency JSON",
            json.dumps(results, ensure_ascii=False, indent=2),
            file_name="latency_benchmark_results.json",
            mime="application/json",
        )

with tab_ocr:
    st.subheader("PDF ingestion and OCR pilot")
    st.caption("Mistral OCR output is saved separately and does not overwrite baseline Markdown.")
    baseline_md_files = [
        PROJECT_DIR / "data" / "standardized" / "legal" / "luat-phong-chong-ma-tuy-2021.md",
        PROJECT_DIR / "data" / "standardized" / "legal" / "nghi-dinh-105-2021.md",
    ]
    st.markdown("**Baseline Markdown quality diagnostics**")
    st.dataframe([inspect_markdown_quality(path) for path in baseline_md_files if path.exists()], use_container_width=True)

    if st.button("Chạy Mistral OCR pilot"):
        if not os.getenv("MISTRAL_API_KEY"):
            st.error("MISTRAL_API_KEY chưa được cấu hình trong .env.")
        else:
            with st.status("Đang chạy Mistral OCR...", expanded=True) as status:
                results = run_pilot(DEFAULT_PILOT_FILES)
                status.update(label="OCR pilot hoàn tất", state="complete")
            st.session_state["ocr_results"] = results

    if st.session_state.get("ocr_results"):
        st.json(st.session_state["ocr_results"])

with tab_config:
    st.subheader("Comparison options")
    st.markdown(
        """
        - Baseline keeps the current local JSON index and hybrid retrieval.
        - PageIndex is intentionally excluded from default benchmarks and evaluations.
        - Jina reranker is optional and only used when `JINA_API_KEY` is configured.
        - Mistral OCR is treated as a candidate preprocessing path until metrics justify replacing baseline extraction.
        """
    )
