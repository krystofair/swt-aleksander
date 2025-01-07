"""
    Config processor for structured configs of DB-s.
"""

from typing import List, Union, Any
from dataclasses import dataclass, field
import logging

from hydra import conf


log = logging.getLogger(__name__)


@dataclass
class SqliteConfig:
    _target_: str = "aleksander.dblayer.SqliteConnection"
    path: str = ":memory:"

@dataclass
class PostgresConfig:
    _target_: str = "aleksander.dblayer.PostgreSQLConnection"
    port: int = 5432
    host: str = "localhost"
    user: str = "user"
    password: str = "password"
    dbname: str = "db"

@dataclass
class Config:
    defaults: List[Any] = field(default_factory=lambda: [{"db": "sqlite"}])
    db = conf.MISSING

def prepare_config_store():
    cs = conf.ConfigStore.instance()
    cs.store(name="config", node=Config)
    cs.store(group="db", name="sqlite", node=SqliteConfig)
    cs.store(group="db", name="postgresql", node=PostgresConfig)
    return cs