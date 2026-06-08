from __future__ import annotations

import importlib


def test_chunks_path_changes_for_jina_late(monkeypatch):
    monkeypatch.setenv("CHUNKING_METHOD", "jina_late")
    monkeypatch.setenv("JINA_EMBEDDING_MODEL", "jina-embeddings-v3")

    from src import local_index

    importlib.reload(local_index)

    path = local_index.chunks_path()
    assert path.name == "chunks-jina_late-jina-embeddings-v3.json"


def test_embed_chunks_uses_jina_late_chunking(monkeypatch):
    monkeypatch.setenv("CHUNKING_METHOD", "jina_late")
    monkeypatch.setenv("JINA_API_KEY", "test-key")
    monkeypatch.setenv("JINA_EMBEDDING_MODEL", "jina-embeddings-v3")

    from src import task4_chunking_indexing

    importlib.reload(task4_chunking_indexing)

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": [
                    {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                    {"index": 1, "embedding": [0.4, 0.5, 0.6]},
                ]
            }

    def _fake_post(url, headers=None, json=None, timeout=None):
        assert json["late_chunking"] is True
        assert json["task"] == "retrieval.passage"
        assert json["model"] == "jina-embeddings-v3"
        return _FakeResponse()

    monkeypatch.setattr(task4_chunking_indexing.requests, "post", _fake_post)

    chunks = [
        {"content": "chunk 1", "metadata": {"path": "doc-a.md", "chunk_index": 0}},
        {"content": "chunk 2", "metadata": {"path": "doc-a.md", "chunk_index": 1}},
    ]

    embedded = task4_chunking_indexing.embed_chunks(chunks)

    assert embedded[0]["embedding"] == [0.1, 0.2, 0.3]
    assert embedded[1]["embedding"] == [0.4, 0.5, 0.6]
    assert embedded[0]["metadata"]["embedding_backend"] == "jina_late"


def test_compare_configs_includes_jina_late_chunking(monkeypatch):
    from group_project.evaluation import eval_pipeline

    captured = []

    def _fake_evaluate_config(dataset, config, top_k=5, use_ragas=True):
        captured.append(config["name"])
        return {"name": config["name"], "summary": {}, "rows": [], "evaluator": "local_overlap"}

    monkeypatch.setattr(eval_pipeline, "evaluate_config", _fake_evaluate_config)

    results = eval_pipeline.compare_configs(golden_dataset=[{"question": "q", "expected_answer": ""}], use_ragas=False)

    assert "jina_late_chunking" in results
    assert "jina_late_chunking" in captured
