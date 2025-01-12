"""
    Module with correlation responsibility.
    Named clustering, cause correlation require shared memory.
"""

import hydra
import redis

from . import configs, models


class RedisCache:
    """
        Some REDIS connection utils.
        This will do round-robin of redis instance in the future.
    """
    _instance: redis.Redis = None

    def __init__(self):
        config: configs.RedisConfig|None = self._configure()
        self.host = config.cache.host
        self.port = config.cache.port

    def _configure(self) -> configs.RedisConfig|None:
        """
            Loads configuration from yaml file by hydra.
        """
        cfg = None
        with hydra.initialize(version_base=configs.VERSION_BASE, config_path="configs"):
            cfg = hydra.compose(config_name="redis")  # type: ignore
        if not cfg:
            raise ValueError("Failure of loading configuration for redis.")
        return cfg  # type: ignore

    def instance(self) -> redis.Redis:
        """Returns instance singleton."""
        cls = self.__class__
        if not cls._instance:
            cls._instance = redis.Redis(host=self.host, port=self.port)
        return cls._instance

# TODO: change name this class, but now I can't find out relevant
class ClusterService:
    """
        Manager, who share memory between workers,
        so they can inform themselves whether object was processed before.
    """
    # TODO: Here will be needed CacheKey for it, this logic is not yet standarized.
    #: For placeholder to real key in the future.
    MPID2MID_MAPPING = "id({match_portal_id})"

    def __init__(self, cache: RedisCache) -> None:
        """
            Prepare redis connection, etc.
        """
        self.cache = cache.instance()

    def is_match_already_processed(self, match_id: models.MatchId) -> bool:
        """
            Returns True if specified match was processed before, False otherwise.
            Arguments:
                match_portal_id - from specific statistics portal id.
        """
        return self.is_match_have_that_object(match_id, 'match')

    def sign_match_as_processed(self, match_id: models.MatchId) -> None:
        """
            Save id for being recgonized in the future.
        """
        # this casting types is awful, I do this to be better oriented in the future
        # when I implement class type for match_id.
        self.add_object_type_of_match(str(match_id), 'match')

    def is_match_have_that_object(self, match_id: models.MatchId, object_type: str) -> bool:
        """
            Download match object and check if there is this kind of object as 'loaded'.
        """
        # TODO: here could be some tree builded for correlation in match.
        objects_type_list = self.cache.lrange(str(match_id), 0, -1)
        for otype in objects_type_list:
            if otype == object_type.encode('utf-8'):
                return True
        return False

    def add_object_type_of_match(self, match_portal_id: str, object_type: str) -> None:
        ot = object_type.encode('utf-8')
        self.cache.lpush(match_portal_id, ot)

    def match_portal_id_with_domain(self, match_portal_id) -> models.MatchId:
        """
            Returns match_id if exist for specified match_portal_id.
        """
        mid = self.cache.get(ClusterService.MPID2MID_MAPPING.format(match_portal_id))
        return models.MatchId(mid)

    def bind_match_portal_id_to_domain(self, match_portal_id, match_id) -> None:
        """
            Set in cache portal id to match uuid for application domain.
            This could be refactored to returning new match_id and work as a services. #TODO
        """
        key = ClusterService.MPID2MID_MAPPING.format(match_portal_id)
        self.cache.set(key, match_id)
