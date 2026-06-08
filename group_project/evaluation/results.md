# RAG Evaluation Results

## Overall Scores

| Metric | baseline | disable_llm_query_variants | query_variants_and_hyde_enable | jina_late_chunking |
|---|---:|---:|---:|---:|
| faithfulness | 0.375 | 0.366 | 0.358 | 0.367 |
| answer_relevance | 0.461 | 0.466 | 0.476 | 0.464 |
| context_recall | 0.403 | 0.402 | 0.402 | 0.412 |
| context_precision | 0.062 | 0.064 | 0.064 | 0.068 |
| average | 0.325 | 0.324 | 0.325 | 0.328 |
| latency_ms | 8388.268 | 4258.791 | 10320.101 | 11303.582 |

## Evaluator

- `baseline`: ragas_unavailable_or_missing_api_key
- `disable_llm_query_variants`: ragas_unavailable_or_missing_api_key
- `query_variants_and_hyde_enable`: ragas_unavailable_or_missing_api_key
- `jina_late_chunking`: ragas_unavailable_or_missing_api_key

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