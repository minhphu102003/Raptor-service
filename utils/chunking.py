from typing import Dict, List


def aggregate_chunks(member_ids: List[str], node2chunk_ids: Dict[str, List[str]]) -> List[str]:
    seen, out = set(), []
    for mid in member_ids:
        for cid in node2chunk_ids[mid]:
            if cid not in seen:
                seen.add(cid)
                out.append(cid)
    return out
