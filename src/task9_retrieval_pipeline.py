"""Task 9 - Retrieval pipeline nâng cao."""

from __future__ import annotations

import os
from collections import defaultdict

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"

LEGAL_KEYWORDS = {
    "luật", "điều", "nghị định", "hình phạt", "tội", "pháp luật", "cai nghiện",
    "danh mục", "tiền chất", "tàng trữ", "mua bán", "sử dụng trái phép",
}
NEWS_KEYWORDS = {
    "nghệ sĩ", "ca sĩ", "diễn viên", "người mẫu", "bị bắt", "báo", "vụ việc",
    "chi dân", "an tây", "hữu tín", "sơn ngọc minh", "châu việt cường",
}
CRIMINAL_KEYWORDS = {"hình phạt", "mức án", "khung hình phạt", "tội", "tàng trữ", "mua bán"}
DRUG_SCOPE_KEYWORDS = {
    "ma túy", "ma tuý", "ma tuy", "chất cấm", "tiền chất", "cai nghiện", "nghiện",
    "tàng trữ", "mua bán trái phép", "sử dụng trái phép", "phòng chống ma túy",
    "chi dân", "an tây", "hữu tín", "sơn ngọc minh", "châu việt cường",
}
PROMPT_INJECTION_PATTERNS = {
    "bỏ qua hướng dẫn", "bỏ qua chỉ dẫn", "ignore previous", "ignore all",
    "system prompt", "developer message", "tiết lộ prompt", "hiển thị prompt",
    "in toàn bộ dữ liệu", "liệt kê dataset", "reveal dataset", "jailbreak",
    "đóng vai", "do anything now",
}
SYNONYMS = {
    "ma túy": ["ma tuý", "ma tuy", "chất ma túy", "chất cấm"],
    "cai nghiện": ["điều trị nghiện", "cơ sở cai nghiện", "quản lý sau cai nghiện"],
    "tàng trữ": ["cất giữ", "giữ trái phép", "tàng trữ trái phép"],
    "tiền chất": ["chất tiền ma túy", "hóa chất kiểm soát"],
    "hình phạt": ["mức án", "khung hình phạt", "xử phạt"],
}


def _contains_any(text: str, keywords: set[str]) -> bool:
    normalized = text.lower()
    return any(keyword in normalized for keyword in keywords)


def detect_prompt_injection(query: str) -> bool:
    return _contains_any(query, PROMPT_INJECTION_PATTERNS)


def rag_tool_router(query: str, chat_history: list[dict] | None = None) -> dict:
    """Quyết định cách dùng RAG bằng rule-based router, không lộ CoT thô."""
    if detect_prompt_injection(query):
        return {
            "use_rag": False,
            "domain": "blocked_prompt_injection",
            "filters": None,
            "use_multi_query": False,
            "use_hyde": False,
            "use_query_expansion": False,
            "fusion_method": "rrf",
            "alpha": 0.5,
            "guardrail": "prompt_injection",
            "trace": ["Đã phát hiện yêu cầu có dấu hiệu prompt injection; không truy cập dữ liệu RAG."],
        }

    if not _contains_any(query, DRUG_SCOPE_KEYWORDS):
        return {
            "use_rag": False,
            "domain": "out_of_scope",
            "filters": None,
            "use_multi_query": False,
            "use_hyde": False,
            "use_query_expansion": False,
            "fusion_method": "rrf",
            "alpha": 0.5,
            "guardrail": "out_of_scope",
            "trace": ["Câu hỏi nằm ngoài phạm vi pháp luật ma túy và tin tức liên quan."],
        }

    has_legal = _contains_any(query, LEGAL_KEYWORDS)
    has_news = _contains_any(query, NEWS_KEYWORDS)

    if _contains_any(query, CRIMINAL_KEYWORDS):
        filters = {"type": "legal", "path_contains": "hinh-su"}
        domain = "legal_criminal"
    elif has_legal and not has_news:
        filters = {"type": "legal"}
        domain = "legal"
    elif has_news and not has_legal:
        filters = {"type": "news"}
        domain = "news"
    else:
        filters = None
        domain = "both"

    return {
        "use_rag": True,
        "domain": domain,
        "filters": filters,
        "use_multi_query": True,
        "use_hyde": os.getenv("HYDE_ENABLED", "0") == "1",
        "use_query_expansion": True,
        "fusion_method": os.getenv("FUSION_METHOD", "rrf"),
        "alpha": float(os.getenv("FUSION_ALPHA", "0.5")),
        "trace": [
            f"Đã phân loại câu hỏi thuộc nhóm: {domain}.",
            f"Metadata filter: {filters or 'không áp dụng'}."
        ],
    }


def _openrouter_client():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        return OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        )
    except Exception:
        return None


def _llm_variants(query: str, n: int = 4) -> list[str]:
    client = _openrouter_client()
    if client is None:
        return []
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Tạo các biến thể truy vấn tiếng Việt để tìm kiếm RAG. "
                        "Giữ nguyên ý định, không trả lời câu hỏi. "
                        f"Trả về mỗi dòng một truy vấn, tối đa {n} dòng.\n\nCâu hỏi: {query}"
                    ),
                }
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        return [line.strip("-• \t") for line in content.splitlines() if line.strip()][:n]
    except Exception:
        return []


def _fallback_multi_query(query: str) -> list[str]:
    variants = [query]
    variants.append(f"{query} quy định pháp luật Việt Nam")
    variants.append(f"{query} nguồn báo chí chính thống")
    return variants


def _expand_query(query: str) -> str:
    additions = []
    lower = query.lower()
    for key, values in SYNONYMS.items():
        if key in lower or any(value in lower for value in values):
            additions.extend([key, *values])
    if not additions and ("ma túy" in lower or "ma tuý" in lower or "ma tuy" in lower):
        additions.extend(SYNONYMS["ma túy"])
    return " ".join(dict.fromkeys([query, *additions]))


def _hyde_text(query: str) -> str:
    if os.getenv("HYDE_ENABLED", "0") != "1":
        return ""
    client = _openrouter_client()
    if client is None:
        return ""
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Sinh một đoạn tài liệu giả định ngắn bằng tiếng Việt có thể chứa câu trả lời "
                        "cho truy vấn RAG bên dưới. Không bịa nguồn, không tạo citation giả.\n\n"
                        f"Truy vấn: {query}"
                    ),
                }
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
    except Exception:
        return ""


def transform_query(query: str, mode: str = "auto") -> dict:
    variants = []
    if mode in ("auto", "multi_query"):
        variants.extend(_llm_variants(query) or _fallback_multi_query(query))
    else:
        variants.append(query)

    expanded_variants = []
    for variant in variants:
        expanded_variants.append(_expand_query(variant))

    hyde = _hyde_text(query) if mode in ("auto", "hyde") else ""
    if hyde:
        expanded_variants.append(f"{query}\n{hyde}")

    deduped = list(dict.fromkeys(v for v in expanded_variants if v.strip()))
    return {
        "original_query": query,
        "variants": deduped,
        "hyde": hyde,
        "trace": [
            f"Đã tạo {len(deduped)} biến thể truy vấn.",
            "HyDE đã bật." if hyde else "HyDE không bật hoặc không có API key.",
            "Đã mở rộng truy vấn bằng từ đồng nghĩa/liên quan.",
        ],
    }


def _normalize(results: list[dict]) -> list[dict]:
    if not results:
        return []
    scores = [float(item.get("score", 0.0)) for item in results]
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [{**item, "score": 1.0 if max_score > 0 else 0.0} for item in results]
    return [
        {**item, "score": (float(item.get("score", 0.0)) - min_score) / (max_score - min_score)}
        for item in results
    ]


def _alpha_fusion(dense_results: list[dict], sparse_results: list[dict], top_k: int, alpha: float) -> list[dict]:
    dense = _normalize(dense_results)
    sparse = _normalize(sparse_results)
    items: dict[str, dict] = {}
    scores = defaultdict(float)

    for item in dense:
        metadata = item.get("metadata", {})
        key = f"{metadata.get('path', '')}#{metadata.get('chunk_index', '')}" or item["content"]
        items[key] = item
        scores[key] += alpha * float(item.get("score", 0.0))
    for item in sparse:
        metadata = item.get("metadata", {})
        key = f"{metadata.get('path', '')}#{metadata.get('chunk_index', '')}" or item["content"]
        items[key] = item
        scores[key] += (1 - alpha) * float(item.get("score", 0.0))

    fused = []
    for key, score in sorted(scores.items(), key=lambda pair: pair[1], reverse=True)[:top_k]:
        item = items[key].copy()
        item["score"] = float(score)
        fused.append(item)
    return fused


def _annotate(results: list[dict], method: str, query_variant: str, fusion_method: str, filters: dict | None) -> list[dict]:
    annotated = []
    for item in results:
        updated = item.copy()
        updated["metadata"] = {
            **updated.get("metadata", {}),
            "retrieval_method": method,
            "query_variant": query_variant,
            "fusion_method": fusion_method,
            "metadata_filter": filters or {},
        }
        annotated.append(updated)
    return annotated


def _degradation_event(stage: str, detail: str) -> dict:
    return {"stage": stage, "detail": detail}


def _safe_transform_query(query: str, transformations: str, degradation: list[dict]) -> dict:
    try:
        transformed = transform_query(query, mode=transformations)
        if transformed.get("variants"):
            return transformed
        degradation.append(_degradation_event("query_transform", "Không tạo được biến thể, dùng truy vấn gốc."))
    except Exception as exc:
        degradation.append(_degradation_event("query_transform", f"Lỗi biến đổi truy vấn: {type(exc).__name__}."))
    return {
        "original_query": query,
        "variants": [query],
        "hyde": "",
        "trace": ["Graceful degradation: dùng truy vấn gốc."],
    }


def _safe_search(search_name: str, search_fn, query: str, top_k: int, filters: dict | None, degradation: list[dict]) -> list[dict]:
    try:
        return search_fn(query, top_k=top_k, filters=filters)
    except TypeError:
        try:
            return search_fn(query, top_k=top_k)
        except Exception as exc:
            degradation.append(_degradation_event(search_name, f"Lỗi tìm kiếm: {type(exc).__name__}."))
    except Exception as exc:
        degradation.append(_degradation_event(search_name, f"Lỗi tìm kiếm: {type(exc).__name__}."))
    return []


def _safe_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    top_k: int,
    fusion_method: str,
    alpha: float,
    degradation: list[dict],
) -> list[dict]:
    if not dense_results and not sparse_results:
        degradation.append(_degradation_event("fusion", "Không có kết quả dense hoặc sparse để hợp nhất."))
        return []
    if not dense_results:
        degradation.append(_degradation_event("fusion", "Dense rỗng/lỗi, hạ cấp sang sparse-only."))
        return sparse_results[:top_k]
    if not sparse_results:
        degradation.append(_degradation_event("fusion", "Sparse rỗng/lỗi, hạ cấp sang dense-only."))
        return dense_results[:top_k]

    try:
        if fusion_method == "alpha":
            return _alpha_fusion(dense_results, sparse_results, top_k=top_k, alpha=alpha)
        return rerank_rrf([dense_results, sparse_results], top_k=top_k)
    except Exception as exc:
        degradation.append(_degradation_event("fusion", f"Lỗi hợp nhất {fusion_method}: {type(exc).__name__}; dùng sort theo score."))
        merged = dense_results + sparse_results
        merged.sort(key=lambda item: item.get("score", 0.0), reverse=True)
        return merged[:top_k]


def _safe_rerank(query: str, candidates: list[dict], top_k: int, use_reranking: bool, degradation: list[dict]) -> list[dict]:
    if not candidates:
        return []
    if not use_reranking:
        return candidates[:top_k]
    try:
        return rerank(query, candidates, top_k=top_k, method=RERANK_METHOD)
    except Exception as exc:
        degradation.append(_degradation_event("rerank", f"Lỗi rerank: {type(exc).__name__}; giữ thứ tự fusion."))
        return candidates[:top_k]


def _attach_degradation(results: list[dict], degradation: list[dict]) -> list[dict]:
    for item in results:
        item["metadata"] = {
            **item.get("metadata", {}),
            "degradation": degradation,
        }
    return results


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
    filters: dict | None = None,
    fusion_method: str = "rrf",
    alpha: float = 0.5,
    transformations: str = "auto",
) -> list[dict]:
    if top_k <= 0:
        return []

    degradation: list[dict] = []
    try:
        plan = rag_tool_router(query)
    except Exception as exc:
        degradation.append(_degradation_event("router", f"Lỗi router: {type(exc).__name__}; dùng cấu hình mặc định."))
        plan = {
            "use_rag": True,
            "domain": "unknown",
            "filters": None,
            "fusion_method": "rrf",
            "alpha": 0.5,
            "trace": ["Graceful degradation: router mặc định."],
        }
    active_filters = filters if filters is not None else plan["filters"]
    if not plan.get("use_rag", True):
        return []
    active_fusion = fusion_method or plan["fusion_method"]
    active_alpha = alpha if alpha is not None else plan["alpha"]
    transformed = _safe_transform_query(query, transformations, degradation)

    per_variant_results = []
    for variant in transformed["variants"]:
        dense_results = _safe_search("dense_search", semantic_search, variant, top_k * 2, active_filters, degradation)
        sparse_results = _safe_search("sparse_search", lexical_search, variant, top_k * 2, active_filters, degradation)
        merged = _safe_fusion(
            dense_results,
            sparse_results,
            top_k=top_k * 2,
            fusion_method=active_fusion,
            alpha=active_alpha,
            degradation=degradation,
        )
        per_variant_results.append(_annotate(merged, "hybrid", variant, active_fusion, active_filters))

    try:
        merged = rerank_rrf(per_variant_results, top_k=top_k * 3)
    except Exception as exc:
        degradation.append(_degradation_event("multi_query_fusion", f"Lỗi RRF đa truy vấn: {type(exc).__name__}; nối kết quả."))
        merged = [item for result_list in per_variant_results for item in result_list][:top_k * 3]
    for item in merged:
        item["source"] = "hybrid"

    final_results = _safe_rerank(query, merged, top_k=top_k, use_reranking=use_reranking, degradation=degradation)
    for item in final_results:
        item["source"] = "hybrid"
        item["metadata"] = {
            **item.get("metadata", {}),
            "query_plan": plan,
            "query_transform": transformed,
            "degradation": degradation,
        }

    if not final_results or final_results[0].get("score", 0.0) < score_threshold:
        best_score = final_results[0].get("score", 0.0) if final_results else 0.0
        degradation.append(
            _degradation_event(
                "threshold_fallback",
                f"Điểm hybrid cao nhất {best_score:.3f} thấp hơn ngưỡng {score_threshold:.3f}; chuyển sang PageIndex/local fallback.",
            )
        )
        try:
            fallback = pageindex_search(query, top_k=top_k, filters=active_filters)
        except Exception as exc:
            degradation.append(_degradation_event("pageindex_fallback", f"Lỗi fallback PageIndex/local: {type(exc).__name__}."))
            fallback = []
        for item in fallback:
            item["metadata"] = {
                **item.get("metadata", {}),
                "retrieval_method": "pageindex_fallback",
                "metadata_filter": active_filters or {},
                "query_plan": plan,
                "query_transform": transformed,
                "degradation": degradation,
            }
        if fallback:
            return fallback[:top_k]
        degradation.append(_degradation_event("empty_result", "Không có kết quả nào sau tất cả fallback."))
        return []

    return _attach_degradation(final_results[:top_k], degradation)


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    test_queries = [
        "Hình phạt nào dành cho tội phạm ma túy ở Việt Nam?",
        "Nghệ sĩ nào từng bị bắt vì liên quan đến ma túy?",
        "Luật phòng chống ma túy quy định gì về cai nghiện?",
    ]
    for q in test_queries:
        print(f"\nTruy vấn: {q}")
        for i, r in enumerate(retrieve(q, top_k=3), 1):
            meta = r.get("metadata", {})
            print(f"  {i}. [{r['score']:.3f}] [{r['source']}] {meta.get('source')} - {r['content'][:80]}...")
