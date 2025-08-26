from dataclasses import dataclass
import json
import re
from typing import Dict, List

from langchain_core.output_parsers import StrOutputParser
from underthesea import sent_tokenize as vn_sent_tokenize

from constants.prompt import LLM_EDGE_PROMPT
from services.openai_chat.openai_chat_service import get_edge_decider_llm

try:

    def sentencize(text: str) -> List[str]:
        return [s.strip() for s in vn_sent_tokenize(text) if s.strip()]
except Exception:

    def sentencize(text: str) -> List[str]:
        return [s.strip() for s in re.split(r"(?<=[\.\?\!…])\s+", text) if s.strip()]


@dataclass
class EdgeDecision:
    move_a_to_b: int
    move_b_to_a: int
    rewrite_a_last: str | None
    rewrite_b_first: str | None


def _window_edges(a: str, b: str, k: int = 5) -> Dict[str, List[str]]:
    a_s = sentencize(a)
    b_s = sentencize(b)
    return {
        "a_tail": a_s[-k:],
        "b_head": b_s[:k],
        "a_all": a_s,
        "b_all": b_s,
    }


def enforce_subset(rewrite: str | None, window_tokens: set[str]) -> str | None:
    if not rewrite:
        return None
    toks = set(re.findall(r"\w+|\S", rewrite.lower()))
    return rewrite if toks.issubset(window_tokens) else None


def llm_edge_fix_and_reallocate(
    chunks: List[str],
    llm=None,
    edge_limit: int = 5,
    max_chars_per_chunk: int = 8000,
    max_passes: int = 2,
) -> List[str]:
    """
    Lặp qua các ranh giới (i, i+1), cho LLM quyết định chuyển <=5 câu mỗi mép
    và (nếu cần) viết lại câu đầu/cuối nhưng KHÔNG thêm fact.
    """
    llm = llm or get_edge_decider_llm()
    decide = LLM_EDGE_PROMPT | llm | StrOutputParser()

    passes = 0
    out = chunks[:]
    while passes < max_passes:
        changed = False
        i = 0
        while i < len(out) - 1:
            A, B = out[i], out[i + 1]
            win = _window_edges(A, B, k=edge_limit)

            window_text = " ".join(win["a_tail"] + win["b_head"]).lower()
            window_tokens = set(re.findall(r"\w+|\S", window_text))

            # Gọi LLM
            raw = decide.invoke(
                {"a_tail": "\n".join(win["a_tail"]), "b_head": "\n".join(win["b_head"])}
            )
            try:
                d = json.loads(raw)
                ed = EdgeDecision(
                    move_a_to_b=int(d.get("move_a_to_b", 0)),
                    move_b_to_a=int(d.get("move_b_to_a", 0)),
                    rewrite_a_last=d.get("rewrite_a_last"),
                    rewrite_b_first=d.get("rewrite_b_first"),
                )
            except Exception:
                # Nếu LLM trả về không hợp lệ, bỏ qua ranh giới này
                i += 1
                continue

            # Ràng buộc 0..edge_limit
            ed.move_a_to_b = max(0, min(edge_limit, ed.move_a_to_b))
            ed.move_b_to_a = max(0, min(edge_limit, ed.move_b_to_a))

            a_s = sentencize(A)
            b_s = sentencize(B)

            # 2.1 Chuyển câu theo quyết định (giữ thứ tự, không vượt max_chars)
            take_from_A = min(ed.move_a_to_b, len(a_s))
            take_from_B = min(ed.move_b_to_a, len(b_s))

            new_A = a_s[:-take_from_A] + b_s[:take_from_B]
            new_B = b_s[take_from_B:]
            moved_from_A = a_s[-take_from_A:] if take_from_A else []
            if take_from_B:
                # các câu chuyển từ B sang A đã nhét ở new_A (phần đuôi list)
                pass

            cand_A = " ".join(new_A).strip()
            cand_B = (
                " ".join(new_B + moved_from_A).strip() if take_from_A else " ".join(new_B).strip()
            )

            # Giới hạn kích thước
            if len(cand_A) <= max_chars_per_chunk and len(cand_B) <= max_chars_per_chunk:
                A, B = cand_A, cand_B
                changed = changed or (A != out[i] or B != out[i + 1])

            # 2.2 Viết lại câu đầu/cuối (nếu còn mép bị cắt), nhưng chỉ khi không vượt size
            if ed.rewrite_a_last:
                r = enforce_subset(ed.rewrite_a_last, window_tokens)
                if r:
                    a_list = sentencize(A)
                    if a_list:
                        a_list[-1] = r
                        cand = " ".join(a_list).strip()
                        if len(cand) <= max_chars_per_chunk:
                            A = cand
                            changed = True

            if ed.rewrite_b_first:
                r = enforce_subset(ed.rewrite_b_first, window_tokens)
                if r:
                    b_list = sentencize(B)
                    if b_list:
                        b_list[0] = r
                        cand = " ".join(b_list).strip()
                        if len(cand) <= max_chars_per_chunk:
                            B = cand
                            changed = True

            out[i], out[i + 1] = A, B
            out = [c for c in out if c.strip()]
            i += 1

        if not changed:
            break
        passes += 1

    return out
