from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CognitiveLevel = Literal["beginner", "intermediate", "advanced"]
LearningStyle = Literal["visual", "auditory", "kinesthetic", "reading"]


class StudentCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=50)
    subject: str = Field(min_length=1, max_length=50, description="学习学科，例如 数据结构")
    cognitive_level: CognitiveLevel
    learning_goal: str = Field(min_length=1, description="学习目标，自由文本")
    available_minutes_per_day: int = Field(ge=5, le=600, description="每天可用学习分钟数")
    learning_style: LearningStyle


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    subject: str
    cognitive_level: CognitiveLevel
    learning_goal: str
    available_minutes_per_day: int
    learning_style: LearningStyle
    created_at: datetime
    updated_at: datetime


# ===== 知识点 =====


class ConceptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    subject: str
    prerequisite_codes: list[str]
    description: str | None = None


# ===== 题库 =====


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    concept_code: str
    question_type: str
    stem: str
    choices: dict | list = Field(default_factory=dict)
    answer: str
    difficulty: int
    score: int
    explanation: str | None = None
    source: str | None = None
    year: int | None = None


# ===== Agent / 学习路径相关 =====


class AnswerItem(BaseModel):
    question_id: int = Field(ge=1)
    concept_id: str = Field(min_length=1, description="知识点编码")
    correct: bool
    seconds: int = Field(ge=0, description="作答耗时(秒)")


class DiagnoseRequest(BaseModel):
    student_id: int = Field(ge=1)
    answers: list[AnswerItem] = Field(min_length=1)


class PathItemOut(BaseModel):
    concept_id: str
    title: str
    estimated_minutes: int
    reason: str


class EvaluationScores(BaseModel):
    targeting: int = Field(ge=0, le=10, description="针对性,path 是否聚焦薄弱知识点")
    ordering: int = Field(ge=0, le=10, description="顺序合理性,先修关系是否被尊重")
    feasibility: int = Field(ge=0, le=10, description="可行性,时长是否符合预算")
    personalization: int = Field(ge=0, le=10, description="个性化,是否匹配认知层/风格/目标")
    resource_match: int = Field(ge=0, le=10, description="资源匹配度,title 是否引用真实资源")


class EvaluationOut(BaseModel):
    score: int = Field(ge=0, le=100, description="总分")
    scores: EvaluationScores
    strengths: str | None = None
    improvements: str | None = None
    summary: str | None = None
    mock: bool = Field(default=False, description="是否走了本地启发式兜底")


class DiagnoseResponse(BaseModel):
    student_id: int
    mastery: dict[str, float] = Field(description="知识点掌握度 0~1")
    path: list[PathItemOut]
    reasoning: list[str]
    evaluation: EvaluationOut | None = Field(default=None, description="对本次 path 的客观评价")
    mock: bool = Field(default=False, description="本次响应中是否有 Agent 走了本地 mock 兜底(LLM 不可用时为 true)")


class LearningPathResponse(BaseModel):
    student_id: int
    path: list[PathItemOut]
    mock: bool = False


class InteractionEvent(BaseModel):
    student_id: int = Field(ge=1)
    event: Literal["struggle", "mastered", "skip"] = Field(description="学习交互事件类型")
    concept_id: str = Field(min_length=1)
    detail: str | None = Field(default=None, description="可选自由文本反馈")


class InteractionResponse(BaseModel):
    student_id: int
    path: list[PathItemOut]
    reasoning: list[str]
    mock: bool = False
