"""
    Here you find models for tables in db.
"""
from typing import List

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Sequence,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import (
    relationship,
    mapped_column,
    Mapped,
    DeclarativeBase,
)


class Base(DeclarativeBase):
    pass


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    when = Column(DateTime)
    country = Column(String)
    stadium = Column(String)
    home = Column(String)
    away = Column(String)
    home_score = Column(Integer)
    away_score = Column(Integer)
    referee = Column(String)
    statistics: Mapped[List["Statistic"]] = relationship(back_populates='match')


class Statistic(Base):
    __tablename__ = "statistics"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    name = Column(String)
    home = Column(Float)
    away = Column(Float)
    match = relationship(Match)

__all__ = ["Match", "Statistic"]