# RAG Evaluation Results

## Overall Scores

| Metric | baseline | disable_llm_query_variants | query_variants_and_hyde_enable | jina_late_chunking |
|---|---:|---:|---:|---:|
| faithfulness | 0.373 | 0.362 | 0.361 | 0.386 |
| answer_relevance | 0.464 | 0.473 | 0.461 | 0.449 |
| context_recall | 0.410 | 0.402 | 0.402 | 0.411 |
| context_precision | 0.063 | 0.064 | 0.064 | 0.069 |
| average | 0.328 | 0.325 | 0.322 | 0.329 |
| latency_ms | 5923.555 | 4396.748 | 10380.857 | 5656.993 |

## Evaluator

- `baseline`: ragas_unavailable:ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'
- `disable_llm_query_variants`: ragas_unavailable:ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'
- `query_variants_and_hyde_enable`: ragas_unavailable:ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'
- `jina_late_chunking`: ragas_unavailable:ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'

## Worst Performers

| # | Question | Faithfulness | Relevance | Recall | Precision | Latency ms |
|---|---|---:|---:|---:|---:|---:|
| 1 | Khung hình phạt cơ bản đối với người có hành vi cố ý làm lộ bí mật nhà nước hoặc chiếm đoạt, mua bán, tiêu hủy tài liệu bí mật nhà nước là gì? | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 |
| 2 | Mức phạt tù cao nhất đối với tội vi phạm quy định về an toàn thực phẩm là bao nhiêu năm và áp dụng trong trường hợp nào? | 0.000 | 0.064 | 0.000 | 0.000 | 0.0 |
| 3 | Người nào vô ý làm lộ bí mật nhà nước hoặc làm mất vật, tài liệu bí mật nhà nước thì đối mặt với hình phạt nào tại Khoản 1 Điều 338? | 0.000 | 0.067 | 0.000 | 0.000 | 0.0 |
| 4 | Hành vi gây rối trật tự công cộng thuộc trường hợp nào thì bị phạt tù từ 02 năm đến 07 năm theo quy định tại Điều 318? | 0.000 | 0.100 | 0.000 | 0.000 | 0.0 |
| 5 | Pháp nhân thương mại phạm tội tài trợ khủng bố (Điều 300) thì hình phạt chính được áp dụng như thế nào? | 0.000 | 0.118 | 0.000 | 0.000 | 0.0 |

## Notes

- PageIndex is not part of the default evaluation configs; keep it as a later last-option fallback only.
- `jina_late_chunking` needs `JINA_API_KEY`; otherwise it falls back to local embeddings and the comparison is not a true late-chunking run.
- If RAGAS is unavailable or judge credentials are missing, the script reports local overlap fallback metrics.