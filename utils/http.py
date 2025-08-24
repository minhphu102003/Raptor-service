from typing import Any, Dict, Optional

import requests

from services.fpt_llm.errors import APIError


def parse_retry_after(resp: requests.Response) -> Optional[float]:
    ra = resp.headers.get("Retry-After")
    if not ra:
        return None
    try:
        return float(ra)
    except Exception:
        return None


def safe_json_response(resp: requests.Response) -> Dict[str, Any]:
    try:
        return resp.json()
    except Exception as e:
        raise APIError(f"Invalid JSON response: {e}; body={resp.text[:1000]}")
