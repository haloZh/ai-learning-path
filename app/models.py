from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    cognitive_level: Mapped[str] = mapped_column(String(20), nullable=False)  # beginner/intermediate/advanced
    learning_goal: Mapped[str] = mapped_column(Text, nullable=False)
    available_minutes_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    learning_style: Mapped[str] = mapped_column(String(20), nullable=False)  # visual/auditory/kinesthetic/reading

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
