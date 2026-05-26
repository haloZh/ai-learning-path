"""客观可计算的路径质量指标(对应产品方案 §5)。

与评价 Agent(LLM 主观打分)互补:
- 评价 Agent 输出"亮点 / 改进 / 总评"等可解释短评;
- 这里输出可量化、可批量回归的客观分,适合工程 A/B 对比。
"""

from __future__ import annotations

from collections.abc import Iterable


def path_diversity(path: list[dict]) -> float:
    """路径多样性:不重复 concept_id 占比 ∈ [0,1]。

    越接近 1 表示路径覆盖面广,越接近 0 表示反复推荐同一概念。
    """
    if not path:
        return 0.0
    cids = [p.get("concept_id") for p in path if p.get("concept_id")]
    if not cids:
        return 0.0
    return round(len(set(cids)) / len(cids), 3)


def prerequisite_violation_rate(
    path: list[dict],
    prerequisites: dict[str, list[str]],
) -> float:
    """先修关系违反率:path 中"后修在前、先修在后"的 (a,b) 对 / 总 (a,b) 对。

    假设 prerequisites 形如 { "代数-一元二次方程": ["代数-一元一次方程"] }。
    返回 ∈ [0,1],0 = 完全合规。
    """
    if len(path) < 2:
        return 0.0
    cids = [p.get("concept_id") for p in path if p.get("concept_id")]
    pos = {cid: i for i, cid in enumerate(cids)}
    total = 0
    violated = 0
    for cid in cids:
        for pre in prerequisites.get(cid, []):
            if pre not in pos:
                continue
            total += 1
            if pos[pre] > pos[cid]:
                violated += 1
    if total == 0:
        return 0.0
    return round(violated / total, 3)


def resource_hit_rate(
    path: list[dict],
    resource_pool: dict[str, list[dict]],
) -> float:
    """资源命中率:path 项 title 与 resource_pool 中某条资源 title 完全相同的占比。

    衡量 LLM 是否真的在用 RAG 候选,而不是凭空编造。
    """
    if not path:
        return 0.0
    pool_titles: set[str] = set()
    for items in resource_pool.values():
        for it in items:
            t = (it.get("title") or "").strip()
            if t:
                pool_titles.add(t)
    if not pool_titles:
        return 0.0  # 无候选时无法度量,按 0 处理(分母为空)
    hit = sum(
        1 for p in path if (p.get("title") or "").strip() in pool_titles
    )
    return round(hit / len(path), 3)


def feasibility_ratio(path: list[dict], budget_minutes: int) -> float:
    """可行性比值:总时长 / 预算。

    < 1.0 = 在预算内;1.0–1.3 = 可接受;> 1.3 = 严重超预算。
    """
    if budget_minutes <= 0:
        return 0.0
    total = sum(int(p.get("estimated_minutes") or 0) for p in path)
    return round(total / budget_minutes, 3)


def targeting_score(
    path: list[dict],
    mastery: dict[str, float],
) -> float:
    """针对性:path 项落在 mastery 低的 concept 上的程度 ∈ [0,1]。

    实现:1 - mean(mastery[path_i.concept_id]);找不到 mastery 的项按 0.5 中性处理。
    越接近 1 = 越聚焦薄弱点。
    """
    if not path:
        return 0.0
    vals = []
    for p in path:
        cid = p.get("concept_id")
        v = mastery.get(cid, 0.5) if cid else 0.5
        try:
            v = max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            v = 0.5
        vals.append(v)
    return round(1.0 - sum(vals) / len(vals), 3)


def all_metrics(
    *,
    path: list[dict],
    mastery: dict[str, float],
    prerequisites: dict[str, list[str]],
    resource_pool: dict[str, list[dict]],
    budget_minutes: int,
) -> dict[str, float]:
    """一次性算出全部 5 个客观指标。"""
    return {
        "diversity": path_diversity(path),
        "prereq_violation": prerequisite_violation_rate(path, prerequisites),
        "resource_hit": resource_hit_rate(path, resource_pool),
        "feasibility": feasibility_ratio(path, budget_minutes),
        "targeting": targeting_score(path, mastery),
    }
