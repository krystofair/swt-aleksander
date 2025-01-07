from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .models import *

class DBConnection:

    def connstr(self) -> str:
        return ""
    
    def engine(self) -> Engine:
        return create_engine(self.connstr())


class SqliteConnection(DBConnection):

    def __init__(self, path) -> None:
        self.path = path

    def connstr(self) -> str:
        return "sqlite+pysqlite://{}".format(self.path, self.db)

@dataclass
class PostgreSQLConnection(DBConnection):
    host: str
    port: int
    user: str
    password: str
    dbname: str

    def connstr(self) -> str:
        return ("postgres://{user}:{passwd}@{host}:{port}/{db_name}"
            .format(
                user = self.user,
                passwd = self.password,
                host = self.host,
                port = self.port,
                db_name = self.dbname
            )
        )
