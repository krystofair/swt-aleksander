from typing import TypeVar
from typing import Any


import hydra
import redis

from . import configs, domain

VERSION_BASE = "1.1"


class RedisCache:
    """
        Some REDIS connection utils.
        This will do round-robin of redis instance in the future.
    """
    _instance: redis.Redis = None
    _configured: bool = False

    def __init__(self):
        self.config: configs.RedisConfig = None  # type: ignore
        self._configure()

    def _configure(self):
        """
            Loads configuration from yaml file by hydra.
        """
        cls = self.__class__
        if cls._configured:
            return
        with hydra.initialize(version_base=VERSION_BASE, config_path="configs"):
            self.config = hydra.compose(config_name="redis")  # type: ignore
        if not self.config:
            raise ValueError("Failure of loading configuration for redis.")
        cls._configured = True

    def instance(self) -> redis.Redis:
        """
            Get single instance to do operations
        """
        cls = self.__class__
        if not cls._instance:
            cls._instance = redis.Redis(host=self.config.cache.host, port=self.config.cache.port)
        return cls._instance


class ClusterService:
    """
        Manager, who share memory between workers,
        so they can inform themselves whether object was processed before.
    """
    def __init__(self, cache: RedisCache) -> None:
        """
            Prepare redis connection, etc.
        """
        self.cache = cache.instance()

    def is_match_already_processed(self, match_id: domain.MatchId) -> bool:
        """
            Returns True if specified match was processed before, False otherwise.
            Arguments:
                match_portal_id - from specific statistics portal id.
        """
        return self.is_match_have_that_object(match_id, 'match')

    def sign_match_as_processed(self, match_id: domain.MatchId) -> None:
        """
            Save id for being recgonized in the future.
        """
        # this casting types is awful, I do this to be better oriented in the future
        # when I implement class type for match_id.
        self.add_object_type_of_match(str(match_id), 'match')

    def is_match_have_that_object(self, match_id: domain.MatchId, object_type: str) -> bool:
        """
            Download match object and check if there is this kind of object as 'loaded'.
        """
        objects_type_list = self.cache.lrange(str(match_id), 0, -1)
        for otype in objects_type_list:
            if otype == object_type.encode('utf-8'):
                return True
        return False

    def add_object_type_of_match(self, match_portal_id: str, object_type: str) -> None:
        ot = object_type.encode('utf-8')
        self.cache.lpush(match_portal_id, ot)

    def match_portal_id_with_domain(self, match_portal_id) -> domain.MatchId:
        """
            Returns match_id if exist for specified match_portal_id.
        """
        return domain.MatchId(self.cache.get(match_portal_id))

    def bind_match_portal_id_to_domain(self, match_portal_id, match_id) -> None:
        self.cache.set(match_portal_id, match_id)

