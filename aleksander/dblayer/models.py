"""
    Tables for database in ORM sqlAlchemy style.
    Maybe here will be some mismatch about using concepts like Column descriptors
    with connection to mapped_column. This state should not last so long.
"""
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    DeclarativeBase,
)


class Base(DeclarativeBase):
    pass


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    match_id = Column(String, unique=True)
    when = Column(DateTime)
    country = Column(String)
    stadium = Column(String)
    home = Column(String)
    away = Column(String)
    home_score = Column(Integer)
    away_score = Column(Integer)
    referee = Column(String)
    league = Column(String(64))
    season = Column(String(16))  # 2024/2025; 24/25; or just year 2024; 24


class Statistic(Base):
    __tablename__ = "statistics"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id = Column(String, ForeignKey('matches.match_id'))
    name = Column(String)
    home = Column(Float)
    away = Column(Float)

__all__ = ["Match", "Statistic"]
