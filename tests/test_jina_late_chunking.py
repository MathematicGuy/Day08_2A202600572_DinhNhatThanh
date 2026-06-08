from __future__ import annotations

import importlib
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


class TestJinaLateChunking(unittest.TestCase):
    def test_chunks_path_changes_for_jina_late(self):
        with patch.dict(
            os.environ,
            {"CHUNKING_METHOD": "jina_late", "JINA_EMBEDDING_MODEL": "jina-embeddings-v3"},
            clear=False,
        ):
            from src import local_index

            importlib.reload(local_index)
            path = local_index.chunks_path()

        self.assertEqual(path.name, "chunks-jina_late-jina-embeddings-v3.json")

    def test_embed_chunks_uses_jina_late_chunking(self):
        with patch.dict(
            os.environ,
            {
                "CHUNKING_METHOD": "jina_late",
                "JINA_API_KEY": "test-key",
                "JINA_EMBEDDING_MODEL": "jina-embeddings-v3",
            },
            clear=False,
        ):
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
                self.assertTrue(json["late_chunking"])
                self.assertEqual(json["task"], "retrieval.passage")
                self.assertEqual(json["model"], "jina-embeddings-v3")
                return _FakeResponse()

            chunks = [
                {"content": "chunk 1", "metadata": {"path": "doc-a.md", "chunk_index": 0}},
                {"content": "chunk 2", "metadata": {"path": "doc-a.md", "chunk_index": 1}},
            ]

            with patch.object(task4_chunking_indexing.requests, "post", side_effect=_fake_post):
                embedded = task4_chunking_indexing.embed_chunks(chunks)

        self.assertEqual(embedded[0]["embedding"], [0.1, 0.2, 0.3])
        self.assertEqual(embedded[1]["embedding"], [0.4, 0.5, 0.6])
        self.assertEqual(embedded[0]["metadata"]["embedding_backend"], "jina_late")

    def test_compare_configs_includes_jina_late_chunking(self):
        sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))

        from group_project.evaluation import eval_pipeline

        captured = []

        def _fake_evaluate_config(dataset, config, top_k=5, use_ragas=True):
            captured.append(config["name"])
            return {"name": config["name"], "summary": {}, "rows": [], "evaluator": "local_overlap"}

        with patch.object(eval_pipeline, "evaluate_config", side_effect=_fake_evaluate_config):
            results = eval_pipeline.compare_configs(
                golden_dataset=[{"question": "q", "expected_answer": ""}],
                use_ragas=False,
            )

        self.assertIn("jina_late_chunking", results)
        self.assertIn("jina_late_chunking", captured)


if __name__ == "__main__":
    unittest.main()
