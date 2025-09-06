from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app
from tests.factories import BuildRequestFactory

client = TestClient(app)


def test_build_tree_sync(monkeypatch):
    def fake_summarize(texts: list[str], max_tokens: int) -> str:
        return "\n".join(texts)[:max_tokens]

    def fake_embed(text: str) -> list[float]:
        return [0.0, 1.0, 0.0]

    req = BuildRequestFactory.build()

    res = client.post("/v1/trees:build", content=req.model_dump_json())
    assert res.status_code in (200, 400)  # nosec B101
