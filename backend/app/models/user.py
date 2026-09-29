from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # 访问级别: public / admin / private，决定能检索到哪些文档
    access_level: Mapped[str] = mapped_column(String(20), default="public", nullable=False)
