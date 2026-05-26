"""三 Agent 节点函数。优先调 LLM,失败时降级到本地启发式 mock。"""

import logging

from . import prompts
from .llm import LLMUnavailable, chat_json
from .state import AgentState, PathItem

logger = logging.getLogger(__name__)


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
        "strengths": "(mock) 路径覆盖薄弱知识点",
        "improvements": "(mock) 个性化与资源匹配度无法精细评估",
        "summary": "(mock) 本地启发式评分,LLM 不可用",
    }


# ===== Agent 节点 =====


def diagnose_node(state: AgentState) -> AgentState:
    answers = state.get("answers", [])
    profile = state.get("student_profile", {}) or {}
    reasoning = list(state.get("reasoning", []))
    used_mock = state.get("used_mock", False)

    try:
        result = chat_json(
            prompts.DIAGNOSE_SYSTEM,
            prompts.diagnose_user(profile, answers),
        )
        mastery = {str(k): float(v) for k, v in result.get("mastery", {}).items()}
        if not mastery:
            raise LLMUnavailable("LLM 返回 mastery 为空")
        reasoning.append(f"[diagnose] LLM: {result.get('summary', '').strip()}")
    except LLMUnavailable as e:
        logger.info("diagnose fallback to mock: %s", e)
        mastery, summary = _mock_diagnose(answers)
        reasoning.append(f"[diagnose] mock 兜底({e}): {summary}")
        used_mock = True

    return {**state, "mastery": mastery, "reasoning": reasoning, "used_mock": used_mock}


def _retrieve_resource_pool(mastery: dict[str, float]) -> dict[str, list[dict]]:
    """对掌握度低的前若干个 concept 各检索 top-3 资源,组成 LLM 候选池。"""
    from .rag import get_rag

    if not mastery:
        return {}
    weak_first = sorted(mastery.items(), key=lambda kv: kv[1])[:6]
    rag = get_rag()
    pool: dict[str, list[dict]] = {}
    for cid, score in weak_first:
        hits = rag.retrieve(cid, query=cid, k=3)
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

    try:
        result = chat_json(
            prompts.PLAN_SYSTEM,
            prompts.plan_user(profile, mastery, resource_pool),
        )
        raw_path = result.get("path", [])
        path: list[PathItem] = [
            {
                "concept_id": str(p["concept_id"]),
                "title": str(p["title"]),
                "estimated_minutes": int(p["estimated_minutes"]),
                "reason": str(p["reason"]),
            }
            for p in raw_path
        ]
        if not path:
            raise LLMUnavailable("LLM 返回 path 为空")
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
        score = int(result.get("score", 0))
        scores = {str(k): int(v) for k, v in result.get("scores", {}).items()}
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

    try:
        result = chat_json(
            prompts.OPTIMIZE_SYSTEM,
            prompts.optimize_user(current_path, interaction),
        )
        raw_path = result.get("path", [])
        path: list[PathItem] = [
            {
                "concept_id": str(p["concept_id"]),
                "title": str(p["title"]),
                "estimated_minutes": int(p["estimated_minutes"]),
                "reason": str(p["reason"]),
            }
            for p in raw_path
        ]
        if not path:
            raise LLMUnavailable("LLM 返回 path 为空")
        reasoning.append(f"[optimize] LLM: {result.get('summary', '').strip()}")
    except (LLMUnavailable, KeyError, TypeError, ValueError) as e:
        logger.info("optimize fallback to mock: %s", e)
        path, summary = _mock_optimize(current_path, interaction)
        reasoning.append(f"[optimize] mock 兜底({e}): {summary}")
        used_mock = True

    return {**state, "path": path, "reasoning": reasoning, "used_mock": used_mock}
