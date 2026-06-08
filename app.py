"""Giao diện Streamlit cho RAG chatbot."""

import re

import streamlit as st

from src.task10_generation import generate_with_citation


def _highlight(text: str, query: str) -> str:
    words = [re.escape(w) for w in query.split() if len(w) > 2]
    if not words:
        return text
    return re.sub("(" + "|".join(words) + ")", r"**\1**", text, flags=re.IGNORECASE)


def _display_thought_process(text: str) -> str:
    return text.replace("<thought_process>", "").replace("</thought_process>", "").strip()


st.set_page_config(page_title="RAG Pháp luật ma túy", layout="wide")
st.title("RAG Chatbot về pháp luật ma túy")

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
        result = generate_with_citation(query)
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
        }

    answer = result["answer"]
    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        with st.status("Đang phân tích và kiểm tra câu trả lời...", expanded=True):
            st.markdown(_display_thought_process(result.get("thought_process", "")))
        st.markdown(answer)

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
