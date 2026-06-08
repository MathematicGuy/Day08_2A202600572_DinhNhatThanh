"""Giao diện Streamlit cho RAG chatbot."""

import html
import re

import streamlit as st

from group_project.evaluation.golden_dataset_tools import (
    append_golden_pairs,
    generate_candidate_pairs,
    score_candidate_pairs,
)
from src.task10_generation import generate_with_citation


def _highlight(text: str, query: str) -> str:
    words = [re.escape(w) for w in query.split() if len(w) > 2]
    if not words:
        return text
    return re.sub("(" + "|".join(words) + ")", r"**\1**", text, flags=re.IGNORECASE)


def _display_thought_process(text: str) -> str:
    return text.replace("<thought_process>", "").replace("</thought_process>", "").strip()


def _answer_sentiment(text: str) -> str:
    """Fast local yes/no heuristic used only for UI color."""
    normalized = text.lower().strip()
    negative_markers = (
        "không thể",
        "không có",
        "không tìm thấy",
        "không đủ",
        "chưa thể",
        "ngoài phạm vi",
        "không xác minh",
        "không được",
        "không thuộc",
    )
    positive_markers = (
        "có ",
        "được ",
        "dựa trên",
        "theo ",
        "quy định",
        "có thể",
    )
    if any(marker in normalized for marker in negative_markers):
        return "no"
    if normalized.startswith("có") or any(marker in normalized for marker in positive_markers):
        return "yes"
    return "neutral"


def _render_answer(answer: str) -> None:
    sentiment = _answer_sentiment(answer)
    escaped = html.escape(answer).replace("\n", "<br>")
    st.markdown(
        f'<div class="rag-answer rag-answer-{sentiment}">{escaped}</div>',
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="RAG Pháp luật ma túy", layout="wide")
st.markdown(
    """
    <style>
    .st-emotion-cache-4bm6i2.e1wbovuq4 .rag-answer,
    .rag-answer {
        border-left: 4px solid #94a3b8;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin: 0.25rem 0 0.75rem 0;
        background: rgba(148, 163, 184, 0.10);
    }
    .st-emotion-cache-4bm6i2.e1wbovuq4 .rag-answer-yes,
    .rag-answer-yes {
        border-left-color: #2b9352;
        background: rgba(96, 134, 110, 0.15);
        color: #dee5e1;
    }
    .st-emotion-cache-4bm6i2.e1wbovuq4 .rag-answer-no,
    .rag-answer-no {
        border-left-color: #dc2626;
        background: rgba(220, 38, 38, 0.12);
        color: #991b1b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("RAG Chatbot về pháp luật ma túy")

with st.sidebar.expander("Generate Golden Q&A", expanded=False):
    st.caption("Tạo candidate Q&A, xem metric chất lượng, chọn checkbox rồi submit vào golden dataset.")
    app_pair_count = st.number_input("Số pair", min_value=1, max_value=20, value=3, step=1, key="app-golden-count")
    app_topic_hint = st.text_input("Gợi ý chủ đề", key="app-golden-topic")
    app_use_ragas = st.toggle("Dùng RAGAS nếu khả dụng", value=True, key="app-golden-ragas")

    if st.button("Generate Q&A candidates", key="app-golden-generate"):
        with st.spinner("Đang tạo và chấm candidate pairs..."):
            candidates = generate_candidate_pairs(int(app_pair_count), topic_hint=app_topic_hint)
            st.session_state["app_generated_golden_pairs"] = score_candidate_pairs(candidates, use_ragas=app_use_ragas)

    app_generated_pairs = st.session_state.get("app_generated_golden_pairs", [])
    if app_generated_pairs:
        selected_pairs = []
        for i, pair in enumerate(app_generated_pairs, 1):
            checked = st.checkbox(
                f"{i}. score={pair.get('quality_score', 0):.3f} | {pair.get('question', '')[:55]}",
                value=bool(pair.get("approved")),
                key=f"app-golden-select-{i}",
            )
            with st.popover(f"Xem pair {i}"):
                st.markdown("**Question**")
                st.write(pair.get("question", ""))
                st.markdown("**Expected answer**")
                st.write(pair.get("expected_answer", ""))
                st.markdown("**Expected context**")
                st.write(pair.get("expected_context", ""))
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

        if st.button("Submit selected pairs", key="app-golden-submit"):
            result = append_golden_pairs([{**pair, "approved": True} for pair in selected_pairs], only_approved=True)
            st.success(f"Đã thêm {len(result['appended'])} pairs. Tổng dataset: {result['total']}.")
            if result["skipped"]:
                st.warning(f"Skipped {len(result['skipped'])} pairs.")
            st.session_state.pop("app_generated_golden_pairs", None)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

query = st.chat_input("Nhập câu hỏi về pháp luật ma túy hoặc tin tức liên quan...")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    try:
        with st.status("Đang gọi mô hình và chạy RAG pipeline...", expanded=True) as model_status_box:
            result = generate_with_citation(query)
            model_status = result.get("model_status", {})
            model_name = model_status.get("model_name", "unknown-model")
            if model_status.get("api_call_success"):
                model_status_box.update(label=f"🧠 {model_name} thinking: API call thành công", state="complete")
            else:
                model_status_box.update(
                    label=f"⚠️ {model_name}: {model_status.get('detail', 'fallback hoặc guardrail')}",
                    state="error" if model_status.get("mode") == "llm_error" else "complete",
                )
    except Exception as exc:
        result = {
            "answer": "Xin lỗi, hệ thống đang gặp lỗi khi xử lý câu hỏi. Vui lòng thử lại sau.",
            "sources": [],
            "thought_process": (
                "<thought_process>\n"
                f"- Graceful degradation: app_error: {type(exc).__name__}.\n"
                "- Không hiển thị được nguồn vì pipeline chưa trả kết quả.\n"
                "</thought_process>"
            ),
            "degradation": [{"stage": "app", "detail": f"{type(exc).__name__}: {exc}"}],
            "model_status": {
                "model_name": "unknown-model",
                "api_call_success": False,
                "mode": "app_error",
                "detail": f"{type(exc).__name__}: {exc}",
            },
        }

    answer = result["answer"]
    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        with st.status("Đang phân tích và kiểm tra câu trả lời...", expanded=True):
            st.markdown(_display_thought_process(result.get("thought_process", "")))
        _render_answer(answer)

        if result.get("degradation"):
            with st.expander("Chi tiết graceful degradation", expanded=False):
                st.json(result["degradation"])

        st.subheader("Nguồn đã sử dụng")
        for source in result.get("sources", []):
            meta = source.get("metadata", {})
            title = (
                f"{meta.get('source_label', 'Nguồn tham khảo')} | điểm={source.get('score', 0):.3f} | "
                f"{meta.get('retrieval_method', 'retrieval')} | {meta.get('fusion_method', 'rrf')}"
            )
            with st.expander(title):
                st.json(
                    {
                        "loại": meta.get("type"),
                        "năm": meta.get("year"),
                        "metadata_filter": meta.get("metadata_filter"),
                        "degradation": meta.get("degradation"),
                    },
                    expanded=False,
                )
                st.markdown(_highlight(source.get("content", "")[:1200], query))
