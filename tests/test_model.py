"""Optional external-provider smoke tests.

These tests never contain hardcoded credentials. They skip unless the matching
environment variable is configured in the local `.env` or shell.
"""

from __future__ import annotations

import os

import pytest
import requests
from dotenv import load_dotenv
import json

load_dotenv()


def test_jina_reranker_api_smoke():
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        pytest.skip("JINA_API_KEY is not configured")

    # response = requests.post(
    #     "https://api.jina.ai/v1/rerank",
    #     headers={
    #         "Content-Type": "application/json",
    #         "Authorization": f"Bearer {api_key}",
    #     },
    #     json={
    #         "model": os.getenv("JINA_RERANKER_MODEL", "jinaai/jina-reranker-v2-base-multilingual"),
    #         "query": "hình phạt tàng trữ ma túy",
    #         "top_n": 1,
    #         "documents": [
    #             "Điều luật về tội tàng trữ trái phép chất ma túy.",
    #             "Một bài viết không liên quan đến pháp luật ma túy.",
    #         ],
    #         "return_documents": False,
    #     },
    #     timeout=30,
    # )
    # response.raise_for_status()
    # payload = response.json()
    # assert "results" in payload

    url = "https://api.jina.ai/v1/rerank"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "jina-reranker-v3",
        "query": "hình phạt tàng trữ ma túy",
        "top_n": 3,
        "documents": [
            "Điều luật về tội tàng trữ trái phép chất ma túy.",
            "Một bài viết không liên quan đến pháp luật ma túy.",
        ],
        "return_documents": False
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response.json())
    response.raise_for_status()
    payload = response.json()
    assert "results" in payload




def test_openai_compatible_model_smoke():
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY or OPENAI_API_KEY is not configured")

    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )
    response = client.chat.completions.create(
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        messages=[{"role": "user", "content": "Reply with OK only."}],
        temperature=0,
    )
    assert response.choices[0].message.content


def test_mistral_ocr_client_available():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        pytest.skip("MISTRAL_API_KEY is not configured")

    try:
        from mistralai import Mistral
    except Exception:
        from mistralai.client import Mistral

    client = Mistral(api_key=api_key)
    assert client is not None


test_jina_reranker_api_smoke()