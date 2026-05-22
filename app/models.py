from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    cognitive_level: Mapped[str] = mapped_column(String(20), nullable=False)
    learning_goal: Mapped[str] = mapped_column(Text, nullable=False)
    available_minutes_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    learning_style: Mapped[str] = mapped_column(String(20), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Concept(Base):
    """知识图谱节点。先修关系与人工填写别名都用 JSON 简化。"""

    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    prerequisite_codes: Mapped[list] = mapped_column(JSON, default=list)
    aliases: Mapped[list] = mapped_column(
        JSON,
        default=list,
        doc="[{category, knowledge_point}],用于反查人工填写的命名",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Resource(Base):
    """学习资源(视频/文章/练习集)。concept_code 软关联,demo 阶段不建 FK。"""

    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class Question(Base):
    """题库。stem/choices/explanation 允许 LaTeX 原文,前端用 KaTeX 渲染。"""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    question_type: Mapped[str] = mapped_column(
        String(20), default="single_choice",
        doc="single_choice/multi_choice/true_false/fill_blank/essay",
    )
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[dict | list] = mapped_column(JSON, default=dict, doc="客观题为 dict({A:..}),主观题留空")
    answer: Mapped[str] = mapped_column(String(20), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    score: Mapped[int] = mapped_column(Integer, default=3)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True, doc="真题/模拟/自编")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)


class Interaction(Base):
    """学习交互日志。每次 /interaction 写一行。"""

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event: Mapped[str] = mapped_column(String(20), nullable=False)
    concept_code: Mapped[str] = mapped_column(String(80), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    student: Mapped["Student"] = relationship()


class MasterySnapshot(Base):
    """诊断快照。每次 /diagnose 写一行,保留历史。"""

    __tablename__ = "mastery_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mastery: Mapped[dict] = mapped_column(JSON, default=dict)
    reasoning: Mapped[list] = mapped_column(JSON, default=list)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    student: Mapped["Student"] = relationship()


class LearningPath(Base):
    """每个学生维护一行最新路径(每次 diagnose/interaction 都 upsert)。"""

    __tablename__ = "learning_paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    path: Mapped[list] = mapped_column(JSON, default=list)
    reasoning: Mapped[list] = mapped_column(JSON, default=list)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    student: Mapped["Student"] = relationship()
