"""Streamlit page for visualizing the RAGAS evaluation process."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from group_project.evaluation.eval_pipeline import (  # noqa: E402
    RAW_RESULTS_PATH,
    compare_configs,
    export_results,
    load_golden_dataset,
)
from group_project.evaluation.golden_dataset_tools import (  # noqa: E402
    append_golden_pairs,
    generate_candidate_pairs,
    score_candidate_pairs,
)

st.set_page_config(page_title="RAGAS Evaluation", layout="wide")
st.title("RAGAS Evaluation")

dataset = load_golden_dataset()
eval_tab, generator_tab = st.tabs(["RAGAS evaluation", "Generate golden Q&A"])

with generator_tab:
    st.subheader("Generate thêm Golden Q&A pairs")
    st.caption("Candidate pairs sẽ được chấm metric trước. Bạn chọn checkbox cho những pair muốn thêm vào `golden_dataset.json`.")
    pair_count = st.number_input("Số Golden Q&A pair cần tạo", min_value=1, max_value=20, value=3, step=1)
    topic_hint = st.text_input("Gợi ý chủ đề tùy chọn", placeholder="Ví dụ: cai nghiện bắt buộc, Điều 249, danh mục tiền chất...")
    use_ragas_for_generation = st.toggle("Dùng RAGAS để chấm chất lượng nếu khả dụng", value=True, key="gen_use_ragas")

    if st.button("Generate và chấm chất lượng", type="primary"):
        with st.status("Đang tạo và chấm Golden Q&A candidates...", expanded=True) as status:
            st.write("Tạo candidate pairs theo format golden_dataset.json")
            candidates = generate_candidate_pairs(int(pair_count), topic_hint=topic_hint)
            st.write("Chấm chất lượng bằng RAGAS hoặc local fallback")
            st.session_state["generated_golden_pairs"] = score_candidate_pairs(candidates, use_ragas=use_ragas_for_generation)
            status.update(label="Đã tạo candidates", state="complete")

    generated_pairs = st.session_state.get("generated_golden_pairs", [])
    if generated_pairs:
        st.markdown("**Candidate Q&A pairs**")
        selected_pairs = []
        for i, pair in enumerate(generated_pairs, 1):
            label = (
                f"{i}. score={pair.get('quality_score', 0):.3f} | "
                f"faithfulness={pair.get('faithfulness', 0) or 0:.3f} | "
                f"relevance={pair.get('answer_relevance', 0) or 0:.3f}"
            )
            with st.expander(label, expanded=i == 1):
                checked = st.checkbox("Chọn pair này để thêm vào golden_dataset.json", value=bool(pair.get("approved")), key=f"golden-select-{i}")
                st.markdown("**Question**")
                st.write(pair.get("question", ""))
                st.markdown("**Expected answer**")
                st.write(pair.get("expected_answer", ""))
                st.markdown("**Expected context**")
                st.write(pair.get("expected_context", ""))
                st.markdown("**Quality metrics**")
                st.json(
                    {
                        "quality_evaluator": pair.get("quality_evaluator"),
                        "quality_score": pair.get("quality_score"),
                        "faithfulness": pair.get("faithfulness"),
                        "answer_relevance": pair.get("answer_relevance"),
                        "context_precision": pair.get("context_precision"),
                        "context_recall": pair.get("context_recall"),
                        "ragas_error": pair.get("ragas_error"),
                    }
                )
                if checked:
                    selected_pairs.append(pair)

        st.info(f"Đã chọn {len(selected_pairs)} / {len(generated_pairs)} pairs.")
        if st.button("Submit: thêm selected pairs vào golden_dataset.json"):
            result = append_golden_pairs([{**pair, "approved": True} for pair in selected_pairs], only_approved=True)
            st.success(f"Đã thêm {len(result['appended'])} pairs. Tổng dataset hiện tại: {result['total']}.")
            if result["skipped"]:
                st.warning("Một số pair bị skip.")
                st.json(result["skipped"])
            st.session_state.pop("generated_golden_pairs", None)

with eval_tab:
    dataset = load_golden_dataset()
    limit = st.slider("Số câu hỏi đánh giá", min_value=1, max_value=len(dataset), value=min(5, len(dataset)))
    use_ragas = st.toggle("Dùng RAGAS nếu có API key/thư viện", value=True)

    left, right = st.columns(2)
    with left:
        run_eval = st.button("Chạy đánh giá", type="primary")
    with right:
        load_existing = st.button("Tải kết quả đã lưu")

    results = None
    if run_eval:
        with st.status("Đang chạy evaluation...", expanded=True) as status:
            st.write("Chuẩn bị golden dataset")
            selected_dataset = dataset[:limit]
            st.write("Chạy baseline và optimized config")
            results = compare_configs(golden_dataset=selected_dataset, use_ragas=use_ragas)
            export_results(results)
            status.update(label="Evaluation hoàn tất", state="complete")
    elif load_existing and RAW_RESULTS_PATH.exists():
        results = json.loads(RAW_RESULTS_PATH.read_text(encoding="utf-8"))

    if results:
        st.subheader("Tổng quan")
        cols = st.columns(len(results))
        for col, (name, payload) in zip(cols, results.items()):
            summary = payload.get("summary", {})
            with col:
                st.metric(f"{name} average", f"{summary.get('average', 0):.3f}")
                st.metric("Latency ms", f"{summary.get('latency_ms', 0):.1f}")
                st.caption(f"Evaluator: {payload.get('evaluator', 'unknown')}")

        st.subheader("Metrics theo config")
        st.info(
            "Để thêm config mới, chỉnh `group_project/evaluation/eval_pipeline.py`: "
            "thêm dict config tương tự `BASELINE_CONFIG` hoặc `OPTIMIZED_CONFIG`, rồi truyền vào `compare_configs(configs=[...])`. "
            "Sau đó chạy RAGAS trên page này; kết quả sẽ hiện trong bảng metric theo config."
        )
        metric_rows = []
        for name, payload in results.items():
            row = {"config": name, "evaluator": payload.get("evaluator", "unknown")}
            row.update(payload.get("summary", {}))
            metric_rows.append(row)
        st.dataframe(metric_rows, use_container_width=True)

        st.subheader("Chi tiết từng case")
        selected_config = st.selectbox("Config", list(results.keys()))
        rows = results[selected_config].get("rows", [])
        for i, row in enumerate(rows, 1):
            score = row.get("average", 0.0)
            with st.expander(f"{i}. {row.get('question', '')} | avg={score:.3f} | latency={row.get('latency_ms', 0):.1f}ms"):
                st.markdown("**Answer**")
                st.write(row.get("answer", ""))
                st.markdown("**Ground truth**")
                st.write(row.get("ground_truth", ""))
                st.markdown("**Scores**")
                st.json(
                    {
                        "faithfulness": row.get("faithfulness"),
                        "answer_relevance": row.get("answer_relevance"),
                        "context_precision": row.get("context_precision"),
                        "context_recall": row.get("context_recall"),
                        "average": row.get("average"),
                        "latency_ms": row.get("latency_ms"),
                        "ragas_error": row.get("ragas_error"),
                    }
                )
                st.markdown("**Retrieved contexts**")
                for j, context in enumerate(row.get("contexts", []), 1):
                    st.text_area(f"Context {j}", context[:2000], height=180, key=f"{selected_config}-{i}-{j}")

        st.subheader("Worst performers")
        st.text_area(
            "Giải thích metrics",
            (
                "faithfulness: câu trả lời có bám đúng retrieved contexts không.\n"
                "answer_relevance: câu trả lời có khớp câu hỏi/ground truth không.\n"
                "context_precision: contexts lấy ra có nhiều đoạn thật sự hữu ích không.\n"
                "context_recall: retriever có lấy đủ evidence cần thiết không.\n"
                "average: trung bình các metric chính; score thấp là ứng viên cần xem lại query, chunking, OCR, reranker hoặc dữ liệu nguồn."
            ),
            height=150,
        )
        worst_rows = sorted(results[selected_config].get("rows", []), key=lambda item: item.get("average", 0.0))[:5]
        st.dataframe(
            [
                {
                    "question": row.get("question"),
                    "average": row.get("average"),
                    "faithfulness": row.get("faithfulness"),
                    "answer_relevance": row.get("answer_relevance"),
                    "context_precision": row.get("context_precision"),
                    "context_recall": row.get("context_recall"),
                    "latency_ms": row.get("latency_ms"),
                }
                for row in worst_rows
            ],
            use_container_width=True,
        )

        st.download_button(
            "Download raw JSON",
            json.dumps(results, ensure_ascii=False, indent=2, default=str),
            file_name="ragas_results.json",
            mime="application/json",
        )
    else:
        st.info("Chạy evaluation hoặc tải kết quả đã lưu để xem RAGAS process.")
