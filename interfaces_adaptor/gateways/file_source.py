import asyncio
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx


class FileSourceHybrid:
    def __init__(self, storage_dir: str = "./data/md"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def load_markdown(self, file_bytes: Optional[bytes], file_url: Optional[str]) -> str:
        data = await self._load_bytes(file_bytes, file_url)
        return data.decode("utf-8", errors="ignore")

    async def persist_and_checksum(
        self, file_bytes: Optional[bytes], file_url: Optional[str]
    ) -> Tuple[str, str]:
        """
        - Nếu có file_bytes: dùng trực tiếp.
        - Nếu có file_url: tải về bytes.
        - Persist về storage_dir/<sha256>.md (nếu chưa tồn tại).
        - Trả (source_uri, checksum).
        """
        data = await self._load_bytes(file_bytes, file_url)

        checksum = hashlib.sha256(data).hexdigest()
        path = self.storage_dir / f"{checksum}.md"

        if not path.exists():
            await asyncio.to_thread(path.write_bytes, data)

        source_uri = path.resolve().as_uri()
        return source_uri, checksum

    async def read(self, source_uri: str) -> bytes:
        """
        Đọc nội dung từ source_uri:
        - file://... -> đọc local
        - http(s)://... -> tải lại
        - path thường -> đọc local
        """
        if source_uri.startswith("http://") or source_uri.startswith("https://"):
            async with httpx.AsyncClient() as client:
                resp = await client.get(source_uri, timeout=30)
                resp.raise_for_status()
                return resp.content

        if source_uri.startswith("file://"):
            p = Path(urlparse(source_uri).path)
        else:
            p = Path(source_uri)

        return await asyncio.to_thread(p.read_bytes)

    async def _load_bytes(self, file_bytes: Optional[bytes], file_url: Optional[str]) -> bytes:
        if file_bytes:
            return file_bytes
        if file_url:
            async with httpx.AsyncClient() as client:
                resp = await client.get(file_url, timeout=30)
                resp.raise_for_status()
                return resp.content
        raise ValueError("No file content or file_url provided")
