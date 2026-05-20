"""三 Agent 节点函数。当前为 mock 实现，TODO 标注接 LLM 的位置。"""

from .state import AgentState, PathItem


def diagnose_node(state: AgentState) -> AgentState:
    answers = state.get("answers", [])
    # TODO: 调用 LLM 分析答卷,本版本按答对率粗略估算掌握度
    mastery: dict[str, float] = {}
    counts: dict[str, list[int]] = {}
    for a in answers:
        cid = a["concept_id"]
        counts.setdefault(cid, [0, 0])
        counts[cid][1] += 1
        if a["correct"]:
            counts[cid][0] += 1
    for cid, (right, total) in counts.items():
        mastery[cid] = round(right / total, 2) if total else 0.0

    reasoning = state.get("reasoning", []) + [
        f"[diagnose] 解析 {len(answers)} 道答题,覆盖 {len(mastery)} 个知识点"
    ]
    return {**state, "mastery": mastery, "reasoning": reasoning}


def plan_node(state: AgentState) -> AgentState:
    mastery = state.get("mastery", {})
    # TODO: 调用 LLM 结合知识图谱 + RAG 生成路径,本版本按掌握度排序输出占位项
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

    reasoning = state.get("reasoning", []) + [
        f"[plan] 选取 {len(path)} 个薄弱知识点生成首版路径"
    ]
    return {**state, "path": path, "reasoning": reasoning}


def optimize_node(state: AgentState) -> AgentState:
    interaction = state.get("interaction", {})
    path = list(state.get("path", []))
    # TODO: 调用 LLM 评估近期表现,本版本仅根据 event 类型做最小调整
    event = interaction.get("event")
    if event == "struggle" and path:
        # 卡住:在当前节点后插入一个补强项占位
        cid = interaction.get("concept_id", "?")
        path.insert(
            1,
            {
                "concept_id": cid,
                "title": f"知识点 {cid} 补充练习",
                "estimated_minutes": 20,
                "reason": "用户在该节点反馈吃力,加一组针对性练习",
            },
        )
    elif event == "mastered" and path:
        # 已掌握:跳过当前节点
        path = path[1:]

    reasoning = state.get("reasoning", []) + [
        f"[optimize] 收到 event={event!r},路径长度调整为 {len(path)}"
    ]
    return {**state, "path": path, "reasoning": reasoning}
