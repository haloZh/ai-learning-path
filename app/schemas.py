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


class DiagnoseResponse(BaseModel):
    student_id: int
    mastery: dict[str, float] = Field(description="知识点掌握度 0~1")
    path: list[PathItemOut]
    reasoning: list[str]
    mock: bool = Field(default=True, description="当前是否为 mock 实现")


class LearningPathResponse(BaseModel):
    student_id: int
    path: list[PathItemOut]
    mock: bool = True


class InteractionEvent(BaseModel):
    student_id: int = Field(ge=1)
    event: Literal["struggle", "mastered", "skip"] = Field(description="学习交互事件类型")
    concept_id: str = Field(min_length=1)
    detail: str | None = Field(default=None, description="可选自由文本反馈")


class InteractionResponse(BaseModel):
    student_id: int
    path: list[PathItemOut]
    reasoning: list[str]
    mock: bool = True
