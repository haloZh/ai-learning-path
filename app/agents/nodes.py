"""三 Agent 节点函数。优先调 LLM,失败时降级到本地启发式 mock。"""

import logging

from . import prompts
from .llm import LLMUnavailable, chat_json
from .state import AgentState, PathItem

logger = logging.getLogger(__name__)


# ===== 防御工具 =====


def _get_valid_codes() -> set[str]:
    """从 db 取所有合法 concept_code(作 LLM 输出去幻觉用)。"""
    from app.database import SessionLocal
    from app.models import Concept

    with SessionLocal() as db:
        return {c.code for c in db.query(Concept).all()}


def _clip(value: float, lo: float, hi: float) -> float:
    """把 value 限制到 [lo, hi]。"""
    return max(lo, min(hi, value))


def _normalize_concept_id(cid: str, valid: set[str]) -> str | None:
    """LLM 可能编造不存在的 concept_id;先精确匹配,再尝试最长公共前缀。"""
    if not cid:
        return None
    if cid in valid:
        return cid
    best, best_len = None, 0
    for v in valid:
        prefix_len = 0
        for a, b in zip(cid, v):
            if a != b:
                break
            prefix_len += 1
        if prefix_len > best_len and prefix_len >= 4:
            best, best_len = v, prefix_len
    if best:
        logger.info("concept_id 模糊匹配:%r → %r", cid, best)
    return best


# ===== mock 兜底逻辑(LLM 不可用时启用) =====


def _mock_diagnose(answers: list[dict]) -> tuple[dict[str, float], str]:
    counts: dict[str, list[int]] = {}
    for a in answers:
        cid = a["concept_id"]
        counts.setdefault(cid, [0, 0])
        counts[cid][1] += 1
        if a["correct"]:
            counts[cid][0] += 1
    mastery = {cid: round(r / t, 2) if t else 0.0 for cid, (r, t) in counts.items()}
    return mastery, f"按答对率粗估,覆盖 {len(mastery)} 个知识点"


def _mock_plan(mastery: dict[str, float]) -> tuple[list[PathItem], str]:
    weak_first = sorted(mastery.items(), key=lambda kv: kv[1])
    path: list[PathItem] = [
        {
            "concept_id": cid,
            "title": f"知识点 {cid} 专项强化",
            "estimated_minutes": 30,
            "reason": f"当前掌握度 {score:.0%},优先补强",
        }
        for cid, score in weak_first[:5]
    ]
    return path, f"按掌握度升序选取 {len(path)} 项"


def _mock_optimize(path: list[PathItem], interaction: dict) -> tuple[list[PathItem], str]:
    new_path = list(path)
    event = interaction.get("event")
    cid = interaction.get("concept_id", "?")
    if event == "struggle" and new_path:
        new_path.insert(
            1,
            {
                "concept_id": cid,
                "title": f"知识点 {cid} 补充练习",
                "estimated_minutes": 20,
                "reason": "用户反馈吃力,加一组针对性练习",
            },
        )
    elif event == "mastered" and new_path:
        new_path = [p for p in new_path if p["concept_id"] != cid]
    return new_path, f"按规则处理 event={event!r}"


def _mock_evaluate(
    profile: dict, mastery: dict[str, float], path: list[PathItem]
) -> dict:
    """LLM 不可用时的本地启发式评分:粗略可用,细节差。"""
    targeting = 7
    if mastery and path:
        avg_mastery_in_path = sum(
            mastery.get(p["concept_id"], 0.5) for p in path
        ) / len(path)
        # path 落在 mastery 低的位置 → 高分
        targeting = max(3, min(10, int(round((1 - avg_mastery_in_path) * 12))))

    feasibility = 7
    budget = profile.get("available_minutes_per_day") or 60
    total_min = sum(p.get("estimated_minutes", 0) for p in path)
    if total_min <= budget:
        feasibility = 9
    elif total_min <= budget * 1.3:
        feasibility = 7
    else:
        feasibility = 4

    scores = {
        "targeting": targeting,
        "ordering": 7,
        "feasibility": feasibility,
        "personalization": 6,
        "resource_match": 6,
    }
    total = round(sum(scores.values()) * 2)
    return {
        "score": total,
        "scores": scores,
        "strengths": "路径覆盖薄弱知识点",
        "improvements": "个性化与资源匹配维度暂未精细评估",
        "summary": "由本地启发式策略评分(LLM 暂不可用)",
    }


# ===== Agent 节点 =====


def diagnose_node(state: AgentState) -> AgentState:
    answers = state.get("answers", [])
    profile = state.get("student_profile", {}) or {}
    reasoning = list(state.get("reasoning", []))
    used_mock = state.get("used_mock", False)
    valid_codes = _get_valid_codes()

    try:
        result = chat_json(
            prompts.DIAGNOSE_SYSTEM,
            prompts.diagnose_user(profile, answers),
        )
        # 校验 + clip:LLM 偶尔输出不存在的 concept_id 或越界 mastery
        raw = result.get("mastery", {})
        if not isinstance(raw, dict):
            raise LLMUnavailable(f"LLM 返回 mastery 非 dict: {type(raw).__name__}")
        mastery: dict[str, float] = {}
        dropped = 0
        for k, v in raw.items():
            cid = _normalize_concept_id(str(k), valid_codes)
            if cid is None:
                dropped += 1
                continue
            try:
                mastery[cid] = round(_clip(float(v), 0.0, 1.0), 2)
            except (TypeError, ValueError):
                dropped += 1
        if not mastery:
            raise LLMUnavailable("LLM 返回 mastery 为空或全部无效")
        if dropped:
            reasoning.append(f"[diagnose] 已丢弃 {dropped} 个无效 concept 项")
        reasoning.append(f"[diagnose] LLM: {result.get('summary', '').strip()}")
    except (LLMUnavailable, AttributeError, TypeError, ValueError) as e:
        logger.info("diagnose fallback to mock: %s", e)
        mastery, summary = _mock_diagnose(answers)
        reasoning.append(f"[diagnose] mock 兜底({e}): {summary}")
        used_mock = True

    return {**state, "mastery": mastery, "reasoning": reasoning, "used_mock": used_mock}


def _retrieve_resource_pool(mastery: dict[str, float]) -> dict[str, list[dict]]:
    """对掌握度低的前若干个 concept 各检索 top-3 资源,组成 LLM 候选池。

    RAG 不可用时返回空 dict,不阻塞 plan_node。
    """
    if not mastery:
        return {}
    try:
        from .rag import RagUnavailable, get_rag

        rag = get_rag()
        weak_first = sorted(mastery.items(), key=lambda kv: kv[1])[:6]
        pool: dict[str, list[dict]] = {}
        for cid, _score in weak_first:
            try:
                hits = rag.retrieve(cid, query=cid, k=3)
            except RagUnavailable as e:
                logger.info("rag unavailable for %s: %s", cid, e)
                return {}
            if hits:
                pool[cid] = [
                    {
                        "title": h.get("title", ""),
                        "type": h.get("type", ""),
                        "estimated_minutes": h.get("estimated_minutes", 0),
                        "url": h.get("url", ""),
                    }
                    for h in hits
                ]
        return pool
    except Exception as e:
        logger.warning("resource pool retrieval failed: %s", e)
        return {}


def _get_prerequisites_for(codes: set[str]) -> dict[str, list[str]]:
    """取 codes 涉及的 concept 的先修关系字典(只返回非空的)。"""
    if not codes:
        return {}
    from app.database import SessionLocal
    from app.models import Concept

    out: dict[str, list[str]] = {}
    with SessionLocal() as db:
        rows = db.query(Concept).filter(Concept.code.in_(codes)).all()
        for c in rows:
            pre = c.prerequisite_codes or []
            if pre:
                out[c.code] = pre
    return out


def plan_node(state: AgentState) -> AgentState:
    mastery = state.get("mastery", {})
    profile = state.get("student_profile", {}) or {}
    reasoning = list(state.get("reasoning", []))
    used_mock = state.get("used_mock", False)

    resource_pool = _retrieve_resource_pool(mastery)
    if resource_pool:
        reasoning.append(
            f"[plan] RAG 检索命中 {sum(len(v) for v in resource_pool.values())} 条候选资源"
        )

    valid_codes = _get_valid_codes()
    # 把诊断涉及的 concept 及其先修关系喂给 LLM,让"先修拓扑排序"真用知识图谱
    prerequisites = _get_prerequisites_for(set(mastery.keys()))
    if prerequisites:
        reasoning.append(
            f"[plan] 注入 {len(prerequisites)} 条先修关系(知识图谱)"
        )
    try:
        result = chat_json(
            prompts.PLAN_SYSTEM,
            prompts.plan_user(profile, mastery, resource_pool, prerequisites),
        )
        raw_path = result.get("path", [])
        if not isinstance(raw_path, list):
            raise LLMUnavailable(f"LLM 返回 path 非 list: {type(raw_path).__name__}")
        path: list[PathItem] = []
        dropped = 0
        for p in raw_path:
            if not isinstance(p, dict):
                dropped += 1
                continue
            cid = _normalize_concept_id(str(p.get("concept_id", "")), valid_codes)
            if cid is None:
                dropped += 1
                continue
            try:
                mins = int(_clip(int(p.get("estimated_minutes", 30)), 5, 120))
            except (TypeError, ValueError):
                mins = 30
            path.append({
                "concept_id": cid,
                "title": str(p.get("title", "")).strip() or f"知识点 {cid} 学习",
                "estimated_minutes": mins,
                "reason": str(p.get("reason", "")).strip(),
            })
        if not path:
            raise LLMUnavailable("LLM 返回 path 为空或全部无效")
        if dropped:
            reasoning.append(f"[plan] 已丢弃 {dropped} 个无效 concept 项")
        reasoning.append(f"[plan] LLM: {result.get('summary', '').strip()}")
    except (LLMUnavailable, KeyError, TypeError, ValueError) as e:
        logger.info("plan fallback to mock: %s", e)
        path, summary = _mock_plan(mastery)
        reasoning.append(f"[plan] mock 兜底({e}): {summary}")
        used_mock = True

    return {
        **state,
        "path": path,
        "resource_pool": resource_pool,  # 供 evaluate_node 复用,免二次 RAG
        "reasoning": reasoning,
        "used_mock": used_mock,
    }


def evaluate_node(state: AgentState) -> AgentState:
    """对刚生成的 path 做客观评价,落地为 evaluation 字段供工程持续优化追踪。"""
    profile = state.get("student_profile", {}) or {}
    mastery = state.get("mastery", {})
    path = list(state.get("path", []))
    resource_pool = state.get("resource_pool", {}) or {}
    reasoning = list(state.get("reasoning", []))
    used_mock = state.get("used_mock", False)

    if not path:
        # path 为空(diagnose/plan 全失败)时不评价,避免误打分
        return {**state, "evaluation": {}, "reasoning": reasoning, "used_mock": used_mock}

    try:
        result = chat_json(
            prompts.EVALUATE_SYSTEM,
            prompts.evaluate_user(profile, mastery, path, resource_pool),
        )
        score = int(_clip(int(result.get("score", 0)), 0, 100))
        raw_scores = result.get("scores", {})
        if not isinstance(raw_scores, dict):
            raise LLMUnavailable(f"LLM 返回 scores 非 dict: {type(raw_scores).__name__}")
        scores: dict[str, int] = {}
        for k, v in raw_scores.items():
            try:
                scores[str(k)] = int(_clip(int(v), 0, 10))
            except (TypeError, ValueError):
                continue
        if not scores or score <= 0:
            raise LLMUnavailable("LLM 返回评分缺失或为 0")
        evaluation = {
            "score": score,
            "scores": scores,
            "strengths": str(result.get("strengths", "")).strip(),
            "improvements": str(result.get("improvements", "")).strip(),
            "summary": str(result.get("summary", "")).strip(),
        }
        reasoning.append(
            f"[evaluate] LLM: 总分 {score} - {evaluation['summary']}"
        )
    except (LLMUnavailable, KeyError, TypeError, ValueError) as e:
        logger.info("evaluate fallback to mock: %s", e)
        evaluation = _mock_evaluate(profile, mastery, path)
        reasoning.append(
            f"[evaluate] mock 兜底({e}): 总分 {evaluation['score']}"
        )
        used_mock = True

    return {**state, "evaluation": evaluation, "reasoning": reasoning, "used_mock": used_mock}


def optimize_node(state: AgentState) -> AgentState:
    interaction = state.get("interaction", {}) or {}
    current_path = list(state.get("path", []))
    reasoning = list(state.get("reasoning", []))
    used_mock = state.get("used_mock", False)
    valid_codes = _get_valid_codes()

    try:
        result = chat_json(
            prompts.OPTIMIZE_SYSTEM,
            prompts.optimize_user(current_path, interaction),
        )
        raw_path = result.get("path", [])
        if not isinstance(raw_path, list):
            raise LLMUnavailable(f"LLM 返回 path 非 list: {type(raw_path).__name__}")
        path: list[PathItem] = []
        dropped = 0
        for p in raw_path:
            if not isinstance(p, dict):
                dropped += 1
                continue
            cid = _normalize_concept_id(str(p.get("concept_id", "")), valid_codes)
            if cid is None:
                dropped += 1
                continue
            try:
                mins = int(_clip(int(p.get("estimated_minutes", 30)), 5, 120))
            except (TypeError, ValueError):
                mins = 30
            path.append({
                "concept_id": cid,
                "title": str(p.get("title", "")).strip() or f"知识点 {cid} 学习",
                "estimated_minutes": mins,
                "reason": str(p.get("reason", "")).strip(),
            })
        if not path:
            raise LLMUnavailable("LLM 返回 path 为空或全部无效")
        if dropped:
            reasoning.append(f"[optimize] 已丢弃 {dropped} 个无效 concept 项")
        reasoning.append(f"[optimize] LLM: {result.get('summary', '').strip()}")
    except (LLMUnavailable, KeyError, TypeError, ValueError) as e:
        logger.info("optimize fallback to mock: %s", e)
        path, summary = _mock_optimize(current_path, interaction)
        reasoning.append(f"[optimize] mock 兜底({e}): {summary}")
        used_mock = True

    return {**state, "path": path, "reasoning": reasoning, "used_mock": used_mock}
