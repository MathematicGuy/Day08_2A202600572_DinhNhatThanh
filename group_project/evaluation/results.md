# RAG Evaluation Results

## Overall Scores

| Metric | baseline | optimized_fast |
|---|---:|---:|
| faithfulness | 0.695 | 0.811 |
| answer_relevance | 0.706 | 0.669 |
| context_recall | 0.770 | 0.702 |
| context_precision | 0.107 | 0.101 |
| average | 0.570 | 0.571 |
| latency_ms | 17048.211 | 8311.574 |

## Evaluator

- `baseline`: ragas_unavailable_or_missing_api_key
- `optimized_fast`: ragas_unavailable_or_missing_api_key

## Worst Performers

| # | Question | Faithfulness | Relevance | Recall | Precision | Latency ms |
|---|---|---:|---:|---:|---:|---:|
| 1 | Hình phạt cho tội tàng trữ trái phép chất ma túy theo Điều 249 Bộ luật Hình sự? | 0.718 | 0.556 | 0.676 | 0.128 | 20018.7 |
| 2 | Luật Phòng chống ma túy 2021 quy định những hình thức cai nghiện nào? | 0.671 | 0.857 | 0.864 | 0.086 | 14077.7 |

## Notes

- PageIndex is not part of the default evaluation configs; keep it as a later last-option fallback only.
- If RAGAS is unavailable or judge credentials are missing, the script reports local overlap fallback metrics.