from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Visit(Base):
    """站点访问量计数表（单行）"""
    __tablename__ = "site_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)