"""Helpers to generate, score, and append golden Q&A pairs."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_DIR))

from group_project.evaluation.eval_pipeline import (  # noqa: E402
    GOLDEN_DATASET_PATH,
    _evaluate_rows_with_ragas,
    _local_score_case,
    load_golden_dataset,
)
from src.local_index import ensure_chunks  # noqa: E402
from src.task9_retrieval_pipeline import retrieve  # noqa: E402


def _openai_compatible_client():
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
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


def _extract_json_array(text: str) -> list[dict]:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    payload = json.loads(text)
    if not isinstance(payload, list):
        raise ValueError("Generated payload is not a JSON array")
    return [item for item in payload if isinstance(item, dict)]


def _normalize_pair(item: dict) -> dict:
    return {
        "question": str(item.get("question", "")).strip(),
        "expected_answer": str(item.get("expected_answer", "")).strip(),
        "expected_context": str(item.get("expected_context", "")).strip(),
    }


def _sample_contexts(max_docs: int = 10) -> list[dict]:
    chunks = ensure_chunks()
    selected = []
    seen_sources = set()
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        key = meta.get("source_label") or meta.get("source")
        if key in seen_sources:
            continue
        seen_sources.add(key)
        selected.append(chunk)
        if len(selected) >= max_docs:
            break
    return selected or chunks[:max_docs]


def _fallback_generate_pairs(n: int) -> list[dict]:
    pairs = []
    for chunk in _sample_contexts(max_docs=max(1, n)):
        meta = chunk.get("metadata", {})
        label = meta.get("source_label") or meta.get("source", "nguồn hiện có")
        content = " ".join(chunk.get("content", "").split())
        snippet = content[:450]
        if not snippet:
            continue
        pairs.append(
            {
                "question": f"Nguồn {label} quy định hoặc nêu thông tin gì liên quan đến ma túy?",
                "expected_answer": snippet,
                "expected_context": label,
            }
        )
        if len(pairs) >= n:
            break
    return pairs


def generate_candidate_pairs(n: int, topic_hint: str = "") -> list[dict]:
    """Generate candidate golden Q&A pairs matching golden_dataset.json format."""
    n = max(1, min(int(n), 20))
    contexts = _sample_contexts(max_docs=8)
    context_text = "\n\n---\n\n".join(
        f"Nguồn: {chunk.get('metadata', {}).get('source_label') or chunk.get('metadata', {}).get('source')}\n"
        f"{chunk.get('content', '')[:1200]}"
        for chunk in contexts
    )
    client = _openai_compatible_client()
    if client is None:
        return _fallback_generate_pairs(n)

    prompt = (
        "Tạo bộ golden Q&A tiếng Việt cho đánh giá RAG pháp luật ma túy. "
        "Chỉ dựa trên ngữ cảnh được cung cấp. Không bịa điều luật hoặc nguồn. "
        "Mỗi item phải có đúng 3 field: question, expected_answer, expected_context. "
        f"Tạo đúng {n} item. Trả về JSON array hợp lệ, không thêm giải thích.\n\n"
        f"Gợi ý chủ đề: {topic_hint or 'pháp luật ma túy, cai nghiện, danh mục chất ma túy, tin tức liên quan'}\n\n"
        f"Ngữ cảnh:\n{context_text}"
    )
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        pairs = [_normalize_pair(item) for item in _extract_json_array(content)]
        return [pair for pair in pairs if all(pair.values())][:n] or _fallback_generate_pairs(n)
    except Exception:
        return _fallback_generate_pairs(n)


def score_candidate_pairs(candidates: list[dict], use_ragas: bool = True) -> list[dict]:
    """Score generated pairs before appending them to the golden dataset."""
    scored_rows = []
    for candidate in candidates:
        normalized = _normalize_pair(candidate)
        sources = retrieve(normalized["question"], top_k=5)
        row = {
            "question": normalized["question"],
            "answer": normalized["expected_answer"],
            "contexts": [source.get("content", "") for source in sources],
            "ground_truth": normalized["expected_answer"],
            "expected_context": normalized["expected_context"],
            "sources": sources,
        }
        row.update(_local_score_case(normalized, normalized["expected_answer"], sources))
        scored_rows.append(row)

    evaluator = "local_overlap"
    if use_ragas:
        scored_rows, evaluator = _evaluate_rows_with_ragas(scored_rows)

    output = []
    for candidate, row in zip(candidates, scored_rows):
        item = _normalize_pair(candidate)
        quality_score = float(row.get("average", 0.0))
        item.update(
            {
                "quality_score": quality_score,
                "quality_evaluator": evaluator,
                "faithfulness": row.get("faithfulness"),
                "answer_relevance": row.get("answer_relevance"),
                "context_precision": row.get("context_precision"),
                "context_recall": row.get("context_recall"),
                "approved": quality_score >= 0.5,
                "ragas_error": row.get("ragas_error"),
            }
        )
        output.append(item)
    return output


def append_golden_pairs(candidates: list[dict], only_approved: bool = True, dataset_path: Path = GOLDEN_DATASET_PATH) -> dict:
    dataset = load_golden_dataset()
    existing_questions = {item.get("question", "").strip().lower() for item in dataset}
    appended = []
    skipped = []
    for candidate in candidates:
        if only_approved and not candidate.get("approved", False):
            skipped.append({"question": candidate.get("question"), "reason": "not_approved"})
            continue
        normalized = _normalize_pair(candidate)
        key = normalized["question"].lower()
        if not all(normalized.values()):
            skipped.append({"question": candidate.get("question"), "reason": "missing_required_field"})
            continue
        if key in existing_questions:
            skipped.append({"question": normalized["question"], "reason": "duplicate"})
            continue
        dataset.append(normalized)
        existing_questions.add(key)
        appended.append(normalized)
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"appended": appended, "skipped": skipped, "total": len(dataset)}
