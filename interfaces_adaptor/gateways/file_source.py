from typing import Optional

import aiohttp


class FileSourceHybrid:
    async def load_markdown(self, file_bytes: Optional[bytes], file_url: Optional[str]) -> str:
        if file_bytes:
            return file_bytes.decode("utf-8", errors="ignore")
        if file_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url, timeout=30) as resp:
                    resp.raise_for_status()
                    data = await resp.read()
                    return data.decode("utf-8", errors="ignore")
        raise ValueError("No file content or file_url provided")
