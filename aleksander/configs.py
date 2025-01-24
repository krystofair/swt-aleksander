"""
    Set of structured configs for various of objects, modules, etc.
"""
import os
from typing import List, Union, Any
import logging


import attrs
import hydra
from hydra import conf

from attrs import define, field

VERSION_BASE = "1.1"
    
CONFIG_DIR_PATH = os.environ.get('ALEKSANDER_CONFIG_DIR', None)
if CONFIG_DIR_PATH is None:
    raise ValueError("The variable ALEKSANDER_CONFIG_DIR must be set in environment.")


#: Initialize logging from config
with hydra.initialize_config_dir(version_base=VERSION_BASE, config_dir=CONFIG_DIR_PATH):
    cfg: "DbConfig" = hydra.compose(config_name="aleksander")  # type: ignore
    DEBUG_MODE = cfg.get('debug', False)
    logging.basicConfig(level = logging.DEBUG if DEBUG_MODE else logging.INFO)
    
logging.basicConfig(level=os.environ.get("", None) or logging.INFO)
log = logging.getLogger('aleksander.config')
log.info(f"{CONFIG_DIR_PATH=}")

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
    debug = False


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
