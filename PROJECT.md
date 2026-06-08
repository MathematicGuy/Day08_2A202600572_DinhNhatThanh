# Day 08 RAG Pipeline - Project Notes

## Goal

Finish the individual RAG pipeline, group chatbot/evaluation deliverables, and bonus items with minimum changes to the existing skeleton code.

## Data Sources

### Legal documents

- Luat Phong, chong ma tuy 2021 - Luat so 73/2021/QH14  
  Source: https://congbao.chinhphu.vn/van-ban/nghi-quyet-so-73-2021-qh14-33659.htm
- Nghi dinh 105/2021/ND-CP huong dan Luat Phong, chong ma tuy  
  Source: https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-105-2021-nd-cp-34944/37821.htm
- Nghi dinh 57/2022/ND-CP ve danh muc chat ma tuy va tien chat  
  Source: https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-57-2022-nd-cp-37734.htm
- Nghi dinh 90/2024/ND-CP sua doi danh muc chat ma tuy va tien chat  
  Source: https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-90-2024-nd-cp-42369/51055.htm

### News articles

- Chi Dan and An Tay case, VietnamNet: https://vietnamnet.vn/cong-an-tphcm-thong-tin-vu-2-khoi-to-bat-giu-ca-si-chi-dan-va-nguoi-mau-an-tay-2341921.html
- Son Ngoc Minh case, Thanh Nien: https://thanhnien.vn/ca-si-son-ngoc-minh-vua-bi-bat-vi-lien-quan-den-ma-tuy-la-ai-18526052012481811.htm
- Huu Tin detained, Ngoi Sao/VnExpress: https://ngoisao.vnexpress.net/dien-vien-huu-tin-bi-tam-giu-vi-lien-quan-ma-tuy-4475248.html
- Huu Tin proposed prosecution, VnExpress: https://vnexpress.net/dien-vien-hai-huu-tin-bi-de-nghi-truy-to-7-15-nam-tu-4530802.html
- Chau Viet Cuong case, PLO: https://plo.vn/bat-khan-cap-ca-si-chau-viet-cuong-post473865.html

## Implementation Choices

- Keep public functions from the assignment unchanged.
- Use local JSON cache in `data/index/chunks.json` instead of requiring Docker/Weaviate.
- Use `sentence-transformers/all-MiniLM-L6-v2` when available; otherwise use deterministic hashing embeddings.
- Use BM25 as default lexical search and TF-IDF as the bonus lexical alternative.
- Use hybrid retrieval: dense semantic search plus sparse BM25 search.
- Use RRF fusion by default; optional alpha weighting is available through `FUSION_METHOD=alpha` and `FUSION_ALPHA=0.5`.
- Use metadata pre-filtering for legal/news/criminal-law queries.
- Use PageIndex when `PAGEINDEX_API_KEY` and `PAGEINDEX_INDEX_ID` are configured; otherwise use a local fallback marked as `source="pageindex"`.
- Use OpenRouter through OpenAI-compatible client when `OPENROUTER_API_KEY` is configured; otherwise return an extractive citation fallback.
- HyDE query expansion is available with `HYDE_ENABLED=1`; it uses OpenRouter to create a short hypothetical document before semantic retrieval.
- Multi-Query and rule-based Query Expansion are implemented in `src/task9_retrieval_pipeline.py`.
- Self-correction runs before answers are shown to users. The UI displays a safe `<thought_process>` summary, not raw private chain-of-thought.

## Runbook

```bash
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown
python -m src.task4_chunking_indexing
python -m pytest tests/test_individual.py -v
streamlit run app.py
```

## Bonus Checklist

- TF-IDF lexical search implemented in `src/task6_lexical_search.py`.
- HyDE implemented in `src/task9_retrieval_pipeline.py` and enabled by `HYDE_ENABLED=1`.
- Conversation memory target: Streamlit app keeps chat history in session state.
- UI/UX target: show answer, sources, scores, and snippets.
- Deploy target: Hugging Face Spaces with `OPENROUTER_API_KEY` and PageIndex secrets.
