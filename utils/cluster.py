import logging

logger = logging.getLogger("cluster")


def handle_small_input(X, n, min_k, loglvl):
    if n == 0:
        logger.log(loglvl, "[CLUSTER] Empty input -> []")
        return []
    if n <= min_k or n <= 3:
        logger.log(loglvl, "[CLUSTER] small n fallback -> single cluster with %d points", n)
        return [list(range(n))]
    return None


def assign_small_group(gi, member_idx, all_local_ids, total_local_clusters, reduction_dim, loglvl):
    if len(member_idx) >= 2:
        for idx in member_idx:
            all_local_ids[idx].append(total_local_clusters)
        total_local_clusters += 1
        logger.log(
            loglvl,
            "[CLUSTER] Global group %d -> kept as one local cluster (size=%d)",
            gi,
            len(member_idx),
        )
    else:
        idx_single = member_idx[0]
        all_local_ids[idx_single].append(total_local_clusters)
        total_local_clusters += 1
        logger.log(loglvl, "[CLUSTER] Global group %d -> skipped singleton", gi)
    return total_local_clusters


def prune_and_find_orphans(groups):
    sizes = [len(g) for g in groups]
    multi_ids = [gi for gi, s in enumerate(sizes) if s >= 2]
    singleton_ids = [gi for gi, s in enumerate(sizes) if s == 1]

    covered_by_multi = set()
    for gi in multi_ids:
        covered_by_multi.update(groups[gi])

    redundant_singleton_ids = {gi for gi in singleton_ids if groups[gi][0] in covered_by_multi}
    groups_pruned = [g for gi, g in enumerate(groups) if gi not in redundant_singleton_ids]

    sizes2 = [len(g) for g in groups_pruned]
    multi_ids2 = [gi for gi, s in enumerate(sizes2) if s >= 2]
    singleton_ids2 = [gi for gi, s in enumerate(sizes2) if s == 1]

    covered_by_multi2 = set()
    for gi in multi_ids2:
        covered_by_multi2.update(groups_pruned[gi])

    orphan_points = [
        groups_pruned[gi][0]
        for gi in singleton_ids2
        if groups_pruned[gi][0] not in covered_by_multi2
    ]

    meta = {
        "n_groups_raw": len(sizes),
        "n_groups_pruned": len(groups_pruned),
        "n_multi": len(multi_ids2),
        "n_singleton": len(singleton_ids2),
        "orphan_points": orphan_points,
        "redundant_singleton_ids": sorted(
            gi for gi in singleton_ids if groups[gi][0] in covered_by_multi
        ),
    }
    return groups_pruned, orphan_points, meta
