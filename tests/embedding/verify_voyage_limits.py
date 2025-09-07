"""
VoyageAI rate-limit probes (RPM & TPM) after adding a payment method.
- RPM target (Basic): ~2000 RPM
- TPM target (Basic): ~3,000,000 TPM
Models covered: voyage-context-3 (contextualized endpoint), voyage-3-large, voyage-code-3, voyage-2, voyage-lite-2 (embeddings endpoint)
"""

import asyncio
import math
import os
import time
from typing import List, Tuple

from dotenv import load_dotenv
import voyageai

load_dotenv()
API_KEY = os.getenv("VOYAGEAI_KEY")

MODELS = [
    "voyage-context-3",
]


# ---------- helpers ----------
def is_contextual_model(model: str) -> bool:
    return model.strip().lower() == "voyage-context-3"


async def small_request(ac: voyageai.AsyncClient, model: str):
    """A tiny request to probe RPM without consuming TPM."""
    if is_contextual_model(model):
        return await ac.contextualized_embed(inputs=[["x"]], model=model, input_type="document")
    else:
        return await ac.embed(texts=["x"], model=model, input_type="document")


async def big_request(ac: voyageai.AsyncClient, model: str, texts: List[str]):
    """A larger request (many tokens) to probe TPM with low RPM."""
    if is_contextual_model(model):
        return await ac.contextualized_embed(inputs=[texts], model=model, input_type="document")
    else:
        return await ac.embed(texts=texts, model=model, input_type="document")


def synth_text(repeat_chars: int) -> str:
    # simple filler; ~4 chars ~ 1 token (xấp xỉ). Ta sẽ hiệu chỉnh bằng count_tokens.
    return ("x" * repeat_chars) + " "


def pack_texts_for_tokens(
    sync_client: voyageai.Client, total_target_tokens: int, per_text_tokens_goal: int = 2000
) -> List[str]:
    """
    Tạo danh sách texts có tổng ~ total_target_tokens token.
    Dùng count_tokens để hiệu chỉnh cỡ text thực tế quanh per_text_tokens_goal.
    """
    # 1) tạo một text xấp xỉ per_text_tokens_goal
    guess_chars = max(8, per_text_tokens_goal * 4)  # 4 chars ≈ 1 token (thô)
    txt = synth_text(guess_chars)

    # tinh chỉnh để gần per_text_tokens_goal
    # tăng/giảm chiều dài cho đến khi count_tokens gần mục tiêu (±10%)
    def measure(tokens_goal: int, base: str) -> str:
        lo, hi = int(len(base) * 0.5), int(len(base) * 1.5)
        best = base
        best_err = 10**9
        for L in [int(lo + (hi - lo) * k / 6) for k in range(7)]:
            cand = base[: max(8, L)]
            toks = sync_client.count_tokens([cand])
            err = abs(toks - tokens_goal)
            if err < best_err:
                best_err, best = err, cand
        return best

    txt = measure(per_text_tokens_goal, txt)
    per_text_tokens = sync_client.count_tokens([txt])
    if per_text_tokens == 0:
        per_text_tokens = 1

    # 2) số text cần để đạt tổng token
    n = max(1, total_target_tokens // per_text_tokens)
    texts = [txt] * n

    # 3) nếu còn thiếu chút do chia lấy floor, thêm bớt để gần mục tiêu
    deficit = total_target_tokens - sync_client.count_tokens(texts)
    if deficit > per_text_tokens // 2:
        texts.append(txt)

    return texts


async def rpm_probe(ac: voyageai.AsyncClient, model: str) -> Tuple[int, int]:
    """
    Ramp RPS to see where 429 appears.
    Returns: (total_success, total_errors)
    """
    print(f"\n[RPM PROBE] {model}")
    stages = [
        (5, 10),
        (10, 10),
        (15, 10),
        (20, 10),
        (25, 10),
        (30, 10),
        (33, 10),
        (35, 10),
    ]  # (rps, seconds)
    total_ok = total_err = 0
    first_429_rps = None

    for rps, secs in stages:
        print(f"  stage: {rps} rps for {secs}s")
        for _ in range(secs):
            tasks = [asyncio.create_task(small_request(ac, model)) for __ in range(rps)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            ok = sum(1 for r in results if not isinstance(r, Exception))
            err = len(results) - ok
            total_ok += ok
            total_err += err
            # phát hiện 429
            if err and first_429_rps is None:
                first_429_rps = rps
            await asyncio.sleep(1)

    print(
        f"  -> RPM probe done. success={total_ok}, errors={total_err}, first_429_at_rps={first_429_rps}"
    )
    return total_ok, total_err


async def tpm_probe(ac: voyageai.AsyncClient, sync_client: voyageai.Client, model: str):
    """
    Attempt to approach 3M TPM without breaching RPM.
    Strategy: send a few large requests (e.g., 20–40 RPM) whose combined tokens ~= target per minute.
    """
    print(f"\n[TPM PROBE] {model}")
    TARGETS = [2_000_000, 2_600_000, 3_000_000, 3_200_000]  # tăng dần
    per_req_goal = 100_000  # token/req ước tính; sẽ pack bằng count_tokens
    cooldown = 30  # giãn giữa lượt để cửa sổ 1 phút trượt bớt

    for tgt in TARGETS:
        texts = pack_texts_for_tokens(
            sync_client, total_target_tokens=tgt, per_text_tokens_goal=per_req_goal
        )
        est_tokens = sync_client.count_tokens(texts)
        # số req (mỗi req = 1 payload lớn); đặt 20-40 req/phút để RPM << 2000
        # ở đây dùng 20 req/phút nếu est_tokens > 150k, ngược lại gom lại để không tăng RPM.
        reqs_per_minute = (
            20 if est_tokens >= 150_000 else max(5, math.ceil(150_000 / max(1, est_tokens)))
        )
        duration_sec = 60
        interval = duration_sec / reqs_per_minute

        print(
            f"  target≈{tgt:,} tokens/min; per_request≈{est_tokens:,} tokens; rpm≈{reqs_per_minute}"
        )
        errors = 0
        start = time.monotonic()
        sent = 0
        while time.monotonic() - start < duration_sec:
            try:
                await big_request(ac, model, texts)
            except Exception as e:
                errors += 1
                if "rate" in str(e).lower() or "429" in str(e):
                    print("    -> rate limit hit at this target")
                    break
            sent += 1
            await asyncio.sleep(max(0.0, interval))
        print(f"    sent={sent}, errors={errors}")
        # cooldown một chút giữa các mức
        await asyncio.sleep(cooldown)


async def main():
    if not API_KEY:
        print("ERROR: Please set VOYAGEAI_KEY in environment.")
        return
    ac = voyageai.AsyncClient(api_key=API_KEY)
    sc = voyageai.Client(api_key=API_KEY)  # dùng để count_tokens

    print("Voyage AI Rate Limits Verification (post-billing)")
    print("=" * 50)
    print("Note: Docs list Basic limits for these models as 2000 RPM & 3M TPM.\n")

    for m in MODELS:
        try:
            await rpm_probe(ac, m)
            # nghỉ 45s để cửa sổ 1 phút ổn định, tránh nhiễu kết quả TPM
            await asyncio.sleep(45)
            await tpm_probe(ac, sc, m)
        except Exception as e:
            print(f"Error testing {m}: {e}")
        finally:
            # nghỉ giữa các model để làm sạch cửa sổ rate limit
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
