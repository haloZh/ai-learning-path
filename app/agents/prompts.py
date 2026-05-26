"""三 Agent 的 prompt 模板。所有 user 消息都必须以 JSON 形式构造,模型回 JSON。"""

import json

# ===== 诊断 Agent =====

DIAGNOSE_SYSTEM = """你是一名"管综·数学基础"科目诊断专家,任务是基于学生答卷量化各知识点掌握度。

输出严格 JSON,字段:
- mastery: object,key 为知识点 concept_id,value 为 0~1 的掌握度小数(2 位)
- summary: string,一句话总结薄弱环节,中文,不超过 60 字

判分原则:
- 答对率高且用时短 = 掌握度高
- 答错或用时显著超长 = 掌握度低
- 同一 concept_id 多题取综合判断,不是简单平均
"""


def diagnose_user(profile: dict, answers: list[dict]) -> str:
    payload = {
        "profile": {
            "subject": profile.get("subject"),
            "cognitive_level": profile.get("cognitive_level"),
            "learning_style": profile.get("learning_style"),
        },
        "answers": answers,
    }
    return "学生画像与答卷如下,请输出诊断 JSON:\n" + json.dumps(payload, ensure_ascii=False, indent=2)


# ===== 规划 Agent =====

PLAN_SYSTEM = """你是一名学习路径规划师,根据学生掌握度与时间预算输出 3~5 条学习项。

输出严格 JSON,字段:
- path: array,每项含
  - concept_id: string,对应 mastery 中的 key
  - title: string,中文,不超过 20 字,体现具体动作(如"分式方程系数化简专项")
  - estimated_minutes: integer,5~120
  - reason: string,中文,不超过 40 字,说明为什么排这里
- summary: string,一句话总结路径主线,中文,不超过 60 字

排序原则:
- 掌握度低的优先
- 同等掌握度下,先修关系靠前
- 单项时长不超过学生当日可用分钟数
"""


def plan_user(
    profile: dict,
    mastery: dict,
    resource_pool: dict | None = None,
    prerequisites: dict[str, list[str]] | None = None,
) -> str:
    payload = {
        "profile": {
            "subject": profile.get("subject"),
            "cognitive_level": profile.get("cognitive_level"),
            "learning_style": profile.get("learning_style"),
            "available_minutes_per_day": profile.get("available_minutes_per_day"),
            "learning_goal": profile.get("learning_goal"),
        },
        "mastery": mastery,
    }
    if prerequisites:
        # 把"哪些 concept 先修于哪些 concept"显式喂给 LLM,确保排序合理
        payload["prerequisites"] = prerequisites
    if resource_pool:
        payload["resource_pool"] = resource_pool
        hint = (
            "学生画像、诊断结果"
            + ("、知识图谱先修关系" if prerequisites else "")
            + "与候选资源池如下,请输出路径 JSON。"
            "注意:① title 应与某条候选资源 title 对齐(尽量直接引用其原标题)"
            ",reason 中可点出为什么选这条资源;"
            "② 严格遵守 prerequisites 中的先修关系——若 A 是 B 的先修,A 必须排在 B 之前:\n"
        )
    else:
        hint = (
            "学生画像、诊断结果"
            + ("、知识图谱先修关系" if prerequisites else "")
            + "如下,请输出路径 JSON。"
            + ("严格遵守 prerequisites 先修在前的顺序约束:\n" if prerequisites else ":\n")
        )
    return hint + json.dumps(payload, ensure_ascii=False, indent=2)


# ===== 优化 Agent =====

OPTIMIZE_SYSTEM = """你是一名学习路径动态调整器,根据学生最新交互对当前路径做最小必要调整。

输出严格 JSON,字段:
- path: array,与输入 path 同结构(concept_id/title/estimated_minutes/reason)
- summary: string,一句话说明做了什么调整,中文,不超过 60 字

调整原则:
- event=struggle:在该 concept_id 节点后插入一项补强练习,reason 体现"针对性"
- event=mastered:跳过该 concept_id 节点;若后续节点依赖它,也可标注以加深巩固
- event=skip:把该节点移到路径末尾作为复习项
- 不要无端重写整条路径;尽量只动 1~2 个位置
"""


def optimize_user(path: list[dict], interaction: dict) -> str:
    payload = {"current_path": path, "interaction": interaction}
    return "当前路径与最新交互如下,请输出调整后的 path JSON:\n" + json.dumps(
        payload, ensure_ascii=False, indent=2
    )


# ===== 评价 Agent =====

EVALUATE_SYSTEM = """你是一名学习路径质量审核专家,任务是对刚生成的学习路径做客观评价。

输出严格 JSON,字段:
- score: integer 0-100, 总分
- scores: object, 5 个维度各 0-10:
    - targeting: 针对性, path 是否聚焦在 mastery 较低的知识点上
    - ordering: 顺序合理性, 先修关系是否得到尊重(如等差应在等比之前)
    - feasibility: 可行性, 单项时长 5-120, 总时长应 ≤ 学生当日预算的 1.3 倍
    - personalization: 个性化, 是否与认知层 / 学习风格 / 目标匹配
    - resource_match: 资源匹配度, path 的 title 是否引用了 resource_pool 中的真实资源
- strengths: string, 中文 ≤ 50 字, 本路径亮点
- improvements: string, 中文 ≤ 50 字, 本路径待改进
- summary: string, 中文 ≤ 40 字, 一句话总评

评分原则:
- 客观、可解释,不刷分;扣分点在 improvements 里指出
- targeting: path 项 80% 以上落在 mastery 高的 concept 上 → ≤4 分
- ordering: 出现先修在后修之后 → ≤6 分
- feasibility: 总时长超出预算 30% 以上 → ≤5 分
- personalization: path 完全无视 cognitive_level / learning_style → ≤5 分
- resource_match:
    - title 与 resource_pool 高度对齐(原文复用) → 9-10
    - 仅部分项命中 → 5-7
    - resource_pool 为空时该维度按 7 分中性处理(避免无资源时不公平扣分)
- 总分 = round((targeting + ordering + feasibility + personalization + resource_match) * 2)
"""


def evaluate_user(
    profile: dict,
    mastery: dict,
    path: list[dict],
    resource_pool: dict | None,
) -> str:
    payload = {
        "profile": {
            "subject": profile.get("subject"),
            "cognitive_level": profile.get("cognitive_level"),
            "learning_style": profile.get("learning_style"),
            "available_minutes_per_day": profile.get("available_minutes_per_day"),
            "learning_goal": profile.get("learning_goal"),
        },
        "mastery": mastery,
        "path": path,
        "resource_pool": resource_pool or {},
    }
    return (
        "学生画像、诊断结果、当前路径、候选资源池如下,请输出评价 JSON:\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
