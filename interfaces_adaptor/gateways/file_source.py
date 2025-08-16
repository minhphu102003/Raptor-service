import asyncio
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx

from ..ports import IFileSource


class FileSourceHybrid(IFileSource):
    def __init__(self, storage_dir: str = "./data/md"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def load_markdown(self, file_bytes: Optional[bytes]) -> str:
        return file_bytes.decode("utf-8", errors="ignore")

    async def persist_and_checksum(self, file_bytes: bytes) -> Tuple[str, str]:
        if not file_bytes:
            raise ValueError("file_bytes is required")

        # TODO: replace here upload to s3 in future

        checksum = hashlib.sha256(file_bytes).hexdigest()
        path = self.storage_dir / f"{checksum}.md"

        if not path.exists():
            await asyncio.to_thread(path.write_bytes, file_bytes)

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
