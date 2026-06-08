# RAG Evaluation Results

## Overall Scores

| Metric | baseline | optimized_fast |
|---|---:|---:|
| faithfulness | 0.825 | 0.811 |
| answer_relevance | 0.845 | 0.850 |
| context_recall | 0.872 | 0.856 |
| context_precision | 0.100 | 0.100 |
| average | 0.660 | 0.654 |
| latency_ms | 13021.438 | 10069.171 |

## Evaluator

- `baseline`: ragas_unavailable_or_missing_api_key
- `optimized_fast`: ragas_unavailable_or_missing_api_key

## Worst Performers

| # | Question | Faithfulness | Relevance | Recall | Precision | Latency ms |
|---|---|---:|---:|---:|---:|---:|
| 1 | Hình phạt cho tội tàng trữ trái phép chất ma túy theo Điều 249 Bộ luật Hình sự? | 0.647 | 0.556 | 0.676 | 0.128 | 13744.9 |
| 2 | Danh mục các chất ma túy thuộc nhóm I theo quy định pháp luật Việt Nam gồm những chất nào? | 0.725 | 0.655 | 0.649 | 0.116 | 19784.8 |
| 3 | Luật Phòng chống ma túy 2021 quy định những hình thức cai nghiện nào? | 0.647 | 0.857 | 0.909 | 0.093 | 16729.1 |
| 4 | Ca sĩ nghiện ma túy nổi tiếng nào bị khởi tố, bắt giữ theo thông tin từ Công an TPHCM? | 0.947 | 1.000 | 1.000 | 0.077 | 7811.2 |
| 5 | Nguồn thông tin nào xác nhận việc khởi tố, bắt giữ ca sĩ Chi Dân và người mẫu An Tây? | 0.984 | 1.000 | 1.000 | 0.092 | 10260.6 |

## Notes

- PageIndex is not part of the default evaluation configs; keep it as a later last-option fallback only.
- If RAGAS is unavailable or judge credentials are missing, the script reports local overlap fallback metrics.