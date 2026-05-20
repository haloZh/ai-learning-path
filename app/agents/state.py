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
    answers: list[Answer]
    mastery: dict[str, float]
    path: list[PathItem]
    interaction: dict
    reasoning: list[str]
