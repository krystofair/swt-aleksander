"""
    Set of structured configs for various of objects, modules, etc.
"""

from typing import List, Union, Any
import logging

import attrs
import hydra
from hydra import conf

from attrs import define, field


log = logging.getLogger(__name__)

VERSION_BASE = "1.1"

@define(frozen=True)
class RedisInstance:
    host: str = "locahost"
    port: int = 6379

@define
class RedisConfig:
    cache: RedisInstance = RedisInstance("locahost", 6379)
    broker: RedisInstance = RedisInstance("localhost", 4602)

@define
class SqliteConfig:
    _target_: str
    path: str

@define
class PostgresConfig:
    _target_: str = "aleksander.dblayer.PostgreSQLConnection"
    port: int = 5432
    host: str = "localhost"
    user: str = "user"
    password: str = "password"
    dbname: str = "db"

class DbConfig:
    db = conf.MISSING


@define
class ServicesEntry:
    name = field(type=bytes, converter=lambda x: x.decode('utf-8'))
    topic = field(type=bytes, converter=lambda x: x.decode('utf-8'))
    #: Maybe later, cause there has to be zmq constant resolving.
    # sockopts = field(type=dict)


@define
class Publisher:
    host: str
    port: int


@define
class MainConfig:
    db: str
    publisher: Publisher
    services: list[ServicesEntry]

