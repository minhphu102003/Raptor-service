from __future__ import annotations

import asyncio
from typing import List, Optional, Sequence

import httpx


class OpenAIAPIError(Exception):
    pass


async def call_openai_embeddings(
    api_key: str,
    model: str,
    texts: Sequence[str],
    batch_size: int = 64,
    *,
    timeout: float = 30.0,
    base_url: str = "https://api.openai.com/v1",
    organization: Optional[str] = None,
    dimensions: Optional[int] = None,
    max_retries: int = 3,
) -> List[List[float]]:
    """
    Gọi OpenAI Embeddings /v1/embeddings theo batch và trả về List[List[float]].
    - Nếu 'dimensions' được cung cấp (ví dụ 1536/3072), API sẽ trả vector có đúng số chiều đó
      cho các model text-embedding-3-* (nếu model hỗ trợ). :contentReference[oaicite:1]{index=1}
    """
    if not texts:
        return []

    url = f"{base_url.rstrip('/')}/embeddings"
    headers = {"Authorization": f"Bearer {api_key}"}
    if organization:
        headers["OpenAI-Organization"] = organization

    results: List[List[float]] = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            payload = {"model": model, "input": batch}
            if dimensions is not None:
                payload["dimensions"] = int(dimensions)

            attempt = 0
            while True:
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code >= 400:
                        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                            attempt += 1
                            await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                            continue
                        raise OpenAIAPIError(f"OpenAI error {resp.status_code}: {resp.text}")
                    data = resp.json()
                    # sắp đúng index để tránh xáo trộn
                    batch_vecs: List[Optional[List[float]]] = [None] * len(batch)
                    for item in data.get("data", []):
                        idx = int(item["index"])
                        batch_vecs[idx] = item["embedding"]
                    # phòng hờ trường hợp API thiếu index (hiếm)
                    for i, v in enumerate(batch_vecs):
                        if v is None:
                            raise OpenAIAPIError(
                                "Missing embedding vector in response at index %d" % i
                            )
                    results.extend(batch_vecs)  # type: ignore
                    break
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    if attempt < max_retries:
                        attempt += 1
                        await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                        continue
                    raise OpenAIAPIError(f"HTTP error calling OpenAI: {e}") from e

    return results
