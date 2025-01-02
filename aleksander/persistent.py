from dataclasses import dataclass


@dataclass
class CacheConnection:
    conn_str: str = "redis://localhost:1234"


class CacheMgr(CacheConnection):
    """
        Manager for operation at redis cache.
        This cache clip celery workers together.
    """
    def __init__(self):
        pass

        