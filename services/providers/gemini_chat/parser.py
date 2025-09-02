from typing import Any, Optional, Tuple


def parse_text(resp: Any) -> str:
    out_text = getattr(resp, "text", None)
    if out_text:
        return out_text
    try:
        d = resp.to_dict() if hasattr(resp, "to_dict") else {}
        for c in d.get("candidates") or []:
            parts = (c.get("content") or {}).get("parts") or []
            texts = [p.get("text") for p in parts if isinstance(p, dict) and p.get("text")]
            if texts:
                return "\n".join(texts)
    except Exception:
        pass
    return ""


def finish_info(resp: Any) -> Tuple[Optional[str], Optional[Any]]:
    try:
        cand0 = (getattr(resp, "candidates", None) or [None])[0]
        fr = getattr(cand0, "finish_reason", None)
        pf = getattr(resp, "prompt_feedback", None)
        return fr, pf
    except Exception:
        return None, None
