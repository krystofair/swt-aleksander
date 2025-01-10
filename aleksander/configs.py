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
    _target_: str
    path: str

@dataclass
class PostgresConfig:
    _target_: str = "aleksander.dblayer.PostgreSQLConnection"
    port: int = 5432
    host: str = "localhost"
    user: str = "user"
    password: str = "password"
    dbname: str = "db"

class DbConfig:
    db = conf.MISSING


@dataclass
class MainSocketCfg:
    topic: str
    sockopts: list[str]


@dataclass
class MainConfig:
    sockets: dict
    processors: dict

