import abc
from dataclasses import dataclass

import hydra
from sqlalchemy import create_engine, Engine

from .models import *
from .. import configs

VERSION_BASE = "1.1"


class DbMgr:

    def __init__(self, db_to_use, **engine_kwargs):
        self._cfg = self._configure()
        self.db_connection: DbConn = hydra.utils.instantiate(self._cfg.get(db_to_use))
        self.engine: Engine = create_engine(self.db_connection.connstr(), **engine_kwargs)

    def _configure(self):
        """
            Loads configuration from yaml file by hydra.
        """
        with hydra.initialize_config_dir(version_base=VERSION_BASE, config_dir=configs.CONFIG_DIR_PATH):
            cfg: configs.DbConfig = hydra.compose(config_name="db")  # type: ignore
        if not cfg:
            raise ValueError("Failure of loading configuration for database.")
        return cfg

    @property
    def eng(self):
        return self.engine


class DbConn(abc.ABC):
    def connstr(self) -> str:
        pass

@dataclass
class SqliteConnection(DbConn):
    path: str

    def connstr(self) -> str:
        return "sqlite:///{}".format(self.path)


@dataclass
class PostgreSQLConnection(DbConn):
    host: str
    port: int
    user: str
    password: str
    dbname: str

    def connstr(self) -> str:
        return ("postgresql://{user}:{passwd}@{host}:{port}/{db_name}"
            .format(
                user = self.user,
                passwd = self.password,
                host = self.host,
                port = self.port,
                db_name = self.dbname
            )
        )
