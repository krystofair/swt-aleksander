"""
    Here you find models for tables in db.
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import (
    relationship,
    mapped_column,
    Mapped,
    DeclarativeBase,
)
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Sequence,
    DateTime,
    ForeignKey
)


class Base(DeclarativeBase):
    pass


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, Sequence('match_id'), primary_key=True)
    when = Column(DateTime)
    country = Column(String)
    stadium = Column(String)
    home = Column(String)
    away = Column(String)
    referee = Column(String)
    statistics: Mapped[List["Statistic"]] = relationship(back_populates='match')


class Statistic(Base):
    __tablename__ = "statistics"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    name = Column(String)
    home = Column(Float)
    away = Column(Float)

__all__ = ["Match", "Statistic"]