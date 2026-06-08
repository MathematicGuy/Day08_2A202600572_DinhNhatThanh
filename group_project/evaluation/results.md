# RAG Evaluation Results

## Overall Scores

| Metric | baseline | disable_llm_query_variants | query_variants_and_hyde_enable |
|---|---:|---:|---:|
| faithfulness | 0.380 | 0.364 | 0.353 |
| answer_relevance | 0.468 | 0.444 | 0.480 |
| context_recall | 0.412 | 0.407 | 0.407 |
| context_precision | 0.070 | 0.065 | 0.065 |
| average | 0.333 | 0.320 | 0.327 |
| latency_ms | 10197.902 | 5286.954 | 12289.104 |

## Evaluator

- `baseline`: ragas_unavailable_or_missing_api_key
- `disable_llm_query_variants`: ragas_unavailable_or_missing_api_key
- `query_variants_and_hyde_enable`: ragas_unavailable_or_missing_api_key

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
- If RAGAS is unavailable or judge credentials are missing, the script reports local overlap fallback metrics.