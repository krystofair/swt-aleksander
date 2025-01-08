"""
    Set of structured configs for various of objects, modules, etc.
"""

from typing import List, Union, Any
from dataclasses import dataclass, field
import logging

import hydra
from hydra import conf


log = logging.getLogger(__name__)

VERSION_BASE = "1.1"

@dataclass(frozen=True)
class RedisInstance:
    host: str = "locahost"
    port: int = 6379

@dataclass
class RedisConfig:
    cache: RedisInstance = RedisInstance("locahost", 6379)
    broker: RedisInstance = RedisInstance("localhost", 4602)


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


# nie wiem jak z tym konfigiem tutaj.
# cfg_store = conf.ConfigStore.instance()
# cfg_store.store(name="config", node=Config)
# cfg_store.store(group="db", name="sqlite", node=SqliteConfig)
# cfg_store.store(group="db", name="postgresql", node=PostgresConfig)
# cfg_store.store(group="redis", node=RedisConfig)
