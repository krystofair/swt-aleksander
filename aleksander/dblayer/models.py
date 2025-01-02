"""
    Here you find models for tables in db.
"""

from sqlalchemy import declarative_base
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Sequence
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.schema import MetaData


Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, Sequence('match_id'), primary_key=True)
    when = Column(DateTime)
    country = Column(String)
    stadium = Column(String)
    home = Column(String)
    away = Column(String)
    referee = Column(String)

class Statistic(Base):
    __tablename__ = "statistics"
    match_id = Column(Integer, ForeignKey('matches.id'))
    name = Column(String)  # TODO: this field should have index
    home = Column(Float)
    away = Column(Float)

