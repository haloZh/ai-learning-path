from typing import TypedDict


class Answer(TypedDict):
    question_id: int
    concept_id: str
    correct: bool
    seconds: int


class PathItem(TypedDict):
    concept_id: str
    title: str
    estimated_minutes: int
    reason: str


class AgentState(TypedDict, total=False):
    student_id: int
    student_profile: dict
    answers: list[Answer]
    mastery: dict[str, float]
    path: list[PathItem]
    interaction: dict
    reasoning: list[str]
    used_mock: bool
    # plan_node 写入,evaluate_node 复用,避免二次 RAG 检索
    resource_pool: dict[str, list[dict]]
    # evaluate_node 写入:{score, scores:{...5 dim}, strengths, improvements, summary}
    evaluation: dict
