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
