# Bài Tập Nhóm — Search Engine / RAG Chatbot

## Mục Tiêu

Sau khi hoàn thành bài cá nhân, nhóm ngồi lại để xây dựng **1 trong 2 sản phẩm**:

---

## Yêu cầu 1:  Sản phẩm nhóm RAG Chatbot

Xây dựng chatbot trả lời câu hỏi về pháp luật ma tuý và tin tức liên quan.

**Yêu cầu:**
- Giao diện chat (Streamlit / Gradio / Chainlit)
- Trả lời có citation (dựa trên Task 10)
- Hỗ trợ follow-up questions (conversation memory)
- Hiển thị source documents đã dùng

**Stack gợi ý:**
```
Chainlit/Streamlit → Retrieval (Task 9) → Generation (Task 10) → Display
```

---

## Yêu cầu 2: RAG Evaluation Pipeline

Sử dụng **1 trong 3 framework** sau để evaluate pipeline RAG của nhóm:

### Framework lựa chọn

| Framework | Cài đặt | Đặc điểm |
|-----------|---------|-----------|
| [DeepEval](https://github.com/confident-ai/deepeval) | `pip install deepeval` | Nhiều metric built-in, dễ integrate với pytest |
| [RAGAS](https://github.com/explodinggradients/ragas) | `pip install ragas` | Chuẩn industry cho RAG eval, 3 trục chính |
| [TruLens](https://github.com/truera/trulens) | `pip install trulens` | Dashboard UI, feedback functions mạnh |

### Yêu cầu Evaluation

1. **Tạo Golden Dataset** — tối thiểu 15 cặp Q&A (question, expected_answer, expected_context)
2. **Chạy evaluation** trên toàn bộ golden dataset với các metrics sau:
   - **Faithfulness** — câu trả lời có bám đúng context không?
   - **Answer Relevance** — câu trả lời có đúng câu hỏi không?
   - **Context Recall** — retriever có lấy đủ evidence không?
   - **Context Precision** — trong context lấy về, bao nhiêu % thực sự hữu ích?
3. **So sánh A/B** — chạy eval trên ít nhất 2 config khác nhau (ví dụ: có reranking vs không reranking, hoặc hybrid vs dense-only)
4. **Báo cáo** — bảng điểm + phân tích worst performers + đề xuất cải tiến


### Code mẫu — DeepEval
```python
from deepeval import evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRecallMetric,
    ContextualPrecisionMetric,
)
from deepeval.test_case import LLMTestCase

# Tạo test cases từ golden dataset
test_cases = []
for item in golden_dataset:
    result = rag_pipeline.generate_with_citation(item["question"])
    test_case = LLMTestCase(
        input=item["question"],
        actual_output=result["answer"],
        expected_output=item["expected_answer"],
        retrieval_context=[c["content"] for c in result["sources"]],
    )
    test_cases.append(test_case)

# Chạy evaluation
metrics = [
    FaithfulnessMetric(threshold=0.7),
    AnswerRelevancyMetric(threshold=0.7),
    ContextualRecallMetric(threshold=0.7),
    ContextualPrecisionMetric(threshold=0.7),
]

results = evaluate(test_cases, metrics)
```

### Code mẫu — RAGAS

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from datasets import Dataset

# Chuẩn bị data
eval_data = {
    "question": [],
    "answer": [],
    "contexts": [],
    "ground_truth": [],
}

for item in golden_dataset:
    result = rag_pipeline.generate_with_citation(item["question"])
    eval_data["question"].append(item["question"])
    eval_data["answer"].append(result["answer"])
    eval_data["contexts"].append([c["content"] for c in result["sources"]])
    eval_data["ground_truth"].append(item["expected_answer"])

dataset = Dataset.from_dict(eval_data)

# Chạy evaluation
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
)
print(result.to_pandas())
```

### Code mẫu — TruLens

```python
from trulens.apps.custom import TruCustomApp, instrument
from trulens.core import Feedback
from trulens.providers.openai import OpenAI as TruOpenAI

provider = TruOpenAI()

# Define feedback functions
f_faithfulness = Feedback(provider.groundedness_measure_with_cot_reasons).on_output()
f_relevance = Feedback(provider.relevance).on_input_output()
f_context_relevance = Feedback(provider.context_relevance).on_input()

# Wrap RAG pipeline
tru_rag = TruCustomApp(
    rag_pipeline,
    app_name="DrugLaw_RAG",
    feedbacks=[f_faithfulness, f_relevance, f_context_relevance],
)

# Run evaluation
with tru_rag as recording:
    for item in golden_dataset:
        rag_pipeline.generate_with_citation(item["question"])

# View dashboard
from trulens.dashboard import run_dashboard
run_dashboard()
```

### Deliverable Evaluation

- [x] File `group_project/evaluation/golden_dataset.json` — 15 cặp Q&A
- [x] File `group_project/evaluation/eval_pipeline.py` — script chạy evaluation
- [x] File `group_project/evaluation/results.md` — bảng điểm + phân tích
- [x] So sánh A/B ít nhất 2 configs

---

## Kết Quả Triển Khai Nhóm

Nhóm chọn hướng **RAG Chatbot + RAG Evaluation Pipeline bằng RAGAS**. Hệ thống hiện có:

- Chatbot Streamlit trả lời câu hỏi về pháp luật ma túy và tin tức liên quan.
- Retrieval pipeline hybrid gồm semantic search, BM25 lexical search, RRF/alpha fusion, reranking và fallback có kiểm soát.
- Câu trả lời có citation, hiển thị source documents, metadata, score và degradation logs.
- Golden dataset 15 cặp Q&A trong `group_project/evaluation/golden_dataset.json`.
- Evaluation pipeline trong `group_project/evaluation/eval_pipeline.py`.
- Báo cáo kết quả trong `group_project/evaluation/results.md`.
- Streamlit page riêng để visualize RAGAS/evaluation process và generate thêm golden Q&A candidates.

### Kết Quả Evaluation Hiện Tại

Evaluation đã chạy trên 15 câu hỏi với 4 cấu hình:

| Metric | baseline | disable_llm_query_variants | query_variants_and_hyde_enable | jina_late_chunking |
|---|---:|---:|---:|---:|
| faithfulness | 0.373 | 0.362 | 0.361 | 0.386 |
| answer_relevance | 0.464 | 0.473 | 0.461 | 0.449 |
| context_recall | 0.410 | 0.402 | 0.402 | 0.411 |
| context_precision | 0.063 | 0.064 | 0.064 | 0.069 |
| average | 0.328 | 0.325 | 0.322 | 0.329 |
| latency_ms | 5923.555 | 4396.748 | 10380.857 | 5656.993 |

Ghi chú: môi trường chạy hiện tại chưa import được RAGAS đầy đủ do thiếu `langchain_community.chat_models.vertexai`, nên `eval_pipeline.py` đã fallback sang local-overlap metrics để vẫn so sánh được các cấu hình. Khi cài đủ dependency RAGAS, script sẽ tự dùng RAGAS metrics thật.

### Nhận Xét Nhanh Từ Evaluation

- `jina_late_chunking` đạt average cao nhất trong lần chạy hiện tại: `0.329`, nhưng cần `JINA_API_KEY` để chạy đúng late-chunking/Jina setup.
- `disable_llm_query_variants` có latency tốt nhất trong bảng RAGAS/eval: khoảng `4396 ms`, phù hợp nếu ưu tiên tốc độ.
- `query_variants_and_hyde_enable` chậm nhất: khoảng `10380 ms`, chưa tạo cải thiện score rõ rệt trong lần chạy này.
- Context precision còn thấp, cho thấy retriever lấy nhiều context chưa thật sự hữu ích. Hướng cải thiện: làm sạch OCR/PDF preprocessing, tăng chất lượng golden dataset, thử chunking strategy khác và reranker mạnh hơn.
- Worst performers chủ yếu là các câu ngoài phạm vi ma túy hoặc câu luật hình sự rộng, nên cần bổ sung tài liệu nguồn tương ứng hoặc lọc domain tốt hơn.

## Yêu Cầu Chung

1. **Tích hợp pipeline** từ bài cá nhân của các thành viên
2. **Demo hoạt động được** trong buổi trình bày (chạy local hoặc deploy)
3. **Evaluation pipeline** chạy được và có báo cáo kết quả
4. **Code push lên repository** chung của nhóm
5. **README** mô tả kiến trúc và phân công (điền bên dưới)

---

## Kiến Trúc Hệ Thống

```
Data Collection
  ├─ Legal PDFs: data/landing/legal/
  └─ News JSON/HTML: data/landing/news/
        ↓
Markdown Standardization
  └─ data/standardized/legal + data/standardized/news
        ↓
Chunking + Embedding + Local JSON Index
  └─ data/index/chunks.json
        ↓
Retrieval Pipeline
  ├─ Query router + guardrails
  ├─ Query transform: multi-query / HyDE / synonym expansion
  ├─ Semantic search
  ├─ BM25 lexical search
  ├─ RRF or alpha fusion
  └─ Reranking
        ↓
Generation
  ├─ Context formatting
  ├─ OpenRouter/OpenAI-compatible LLM
  ├─ Citation answer
  └─ Self-correction / graceful degradation
        ↓
Streamlit UI
  ├─ Chatbot page
  ├─ Source display
  ├─ RAGAS Evaluation page
  └─ Golden Q&A generation/review UI
```

PageIndex được giữ là fallback cuối cùng, không dùng mặc định trong evaluation.

---

## Phân Công Công Việc

| Thành viên | MSSV | Nhiệm vụ | Trạng thái |
|-----------|------|----------|------------|
| Lưu Thiện Việt Cường | 2A202600730 | Build group project task 1: tích hợp RAG pipeline, chatbot Streamlit, citation display, source display, conversation memory và UI chính. | Hoàn thành |
| Đinh Nhật Thành | 2A202600572 | Build pipeline evaluation RAGAS, tạo/generate golden dataset, viết `eval_pipeline.py`, tạo `results.md`, thêm UI visualize RAGAS process. | Hoàn thành |
| PhamThiLinhChi | 2A202600748 | Tìm và rà soát tài liệu luật cho golden dataset; đóng góp expected context/expected answer; so sánh các phương pháp retrieval/chunking bằng RAGAS. | Hoàn thành |
| Nguyễn Anh Quân | 2A202600589 | Tìm và rà soát tài liệu luật cho golden dataset; kiểm tra coverage câu hỏi pháp luật; so sánh các phương pháp retrieval/chunking bằng RAGAS. | Hoàn thành |

---

## Hướng Dẫn Chạy

```bash
# Cài dependencies
pip install -r requirements.txt

# Chạy Streamlit chatbot + evaluation pages
streamlit run app.py

# Chạy evaluation pipeline
python group_project/evaluation/eval_pipeline.py

# Xem kết quả evaluation
cat group_project/evaluation/results.md
```

Nếu Streamlit báo lỗi watcher khi import RAGAS/instructor, chạy app từ thư mục project để đọc `.streamlit/config.toml`, hoặc dùng:

```bash
streamlit run app.py --server.fileWatcherType none
```

### File Quan Trọng

- `app.py`: giao diện chatbot chính.
- `pages/1_RAGAS_Evaluation.py`: giao diện visualize RAGAS và generate golden Q&A candidates.
- `group_project/evaluation/golden_dataset.json`: golden dataset 15 Q&A.
- `group_project/evaluation/eval_pipeline.py`: evaluation pipeline.
- `group_project/evaluation/results.md`: báo cáo kết quả.
- `group_project/evaluation/ragas_results.json`: kết quả raw theo từng config.
- `docs/RAG_FLOW.md`: mô tả luồng RAG end-to-end.

### Cách Thêm Config Evaluation

1. Mở `group_project/evaluation/eval_pipeline.py`.
2. Thêm một dict config mới tương tự `BASELINE_CONFIG`, ví dụ thay `RERANK_METHOD`, `HYDE_ENABLED`, `RAG_QUERY_MAX_VARIANTS`, hoặc chunking/embedding env.
3. Truyền config mới vào `compare_configs(configs=[...])` hoặc thêm vào danh sách default.
4. Chạy lại `python group_project/evaluation/eval_pipeline.py` hoặc chạy trên Streamlit RAGAS Evaluation page.

---

## Lưu ý: Hãy giữ lại repo này nếu như bạn học track 3 giai đoạn 2, chúng ta sẽ phát triển tiếp dự án lên knowledge graph để khắc phục các câu hỏi hóc búa khi có các câu hỏi khó.
