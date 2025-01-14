"""
    Module with correlation responsibility.
    Named clustering, cause correlation require shared memory.
"""
import logging
logging.basicConfig()
log=logging.getLogger("clustering")
log.setLevel(logging.DEBUG)
import functools

from . import configs, models, exc

import hydra
import redis
import orjson as jsonlib

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


class CacheKeysMgr:
    """
        Manage keys used in cache - key-value storage.
        Attributes:
            keys: are bytes format to fill
        Methods are for simplified filling keys.
    """
    keys = {
        'delayed': "DELAYED({portal}, {match_portal_id})",
        'match_id': "MATCH_ID({portal}, {match_portal_id})",
        'loaded': "LOADED({match_id}, {typename})"
    }
    def __init__(self, portal_name:str|bytes=None):
        """Allow to fill predefined portal_name parameter for function."""
        self.p = portal_name

    def _check_nullable_portal_name(self, p):
        """
            Safeguard for not do a mistake in form of not set portal_name in constructor
            and not set when called function.
        """
        if not p and not self.p:
            raise ValueError("One of the value has to be filled.")

    def _key(self, subj: str) -> str:
        """
            Helper if cache require specific type of keys.
            Returns converted formatted keys. (Now no needed)
        """
        return subj

    def delayed(self, match_portal_id: str, portal_name: str = None):
        """
            Key for mapping objects' body with their typenames, which will be process in another (internal) task.
        """
        return self._key(self.keys['delayed'].format(
            portal = self._check_nullable_portal_name(portal_name or self.p),
            match_portal_id = match_portal_id
        ))

    def match_id(self, match_portal_id: str, portal_name: str = None):
        return self._key(self.keys['match_id'].format(
            portal=self._check_nullable_portal_name(portal_name or self.p),
            match_portal_id=match_portal_id
        ))

    def loaded(self, match_id: str, typename: str):
        """
            Key for this object which was already saved in database.
        """
        return self._key(self.keys['loaded'].format(
            match_id=match_id,
            typename=typename
        ))

# TODO: change name this class, but now I can't find out relevant
class ClusterService:
    """
        Manager, who share memory between workers,
        so they can inform themselves whether object was processed before.
    """
    # TODO: Here will be needed CacheKey for it, this logic is not yet standarized.
    #: For placeholder to real key in the future.

    def __init__(self, cache: RedisCache) -> None:
        """
            Prepare redis connection, etc.
        """
        self.cache = cache.instance()
        self.key_mgr = CacheKeysMgr("sofascore")  # now using only one portal.

    def check_object_processed(self, mid, typename) -> bool:
        """
            Returns True if match already in database, False otherwise.
        """
        return True if self.cache.get(self.key_mgr.loaded(mid, typename)) else False

    def sign_object_processed(self, match_id: models.MatchId, typename: str) -> None:
        key = self.key_mgr.loaded(str(match_id), typename)
        self.cache.set(key, 1)

    def get_match_id(self, match_portal_id, portal_name=None) -> models.MatchId|None:
        """
            Returns match_id if exist for specified match_portal_id else None.
        """
        cache_key = self.key_mgr.match_id(match_portal_id, portal_name)
        mid = self.cache.get(cache_key)
        return models.MatchId(mid) if mid else None

    def bind_portal_id2match_id(self, match_portal_id, match_id, portal_name=None) -> None:
        """
            Set in cache portal id to match uuid for application domain.
            This could be refactored to returning new match_id and work as a services. #TODO
        """
        key = self.key_mgr.match_id(match_portal_id, portal_name)
        self.cache.set(key, str(match_id))

    def store_temporary(self, obj: models.AbstractObject, portal_name: str = None):
        cache_key = self.key_mgr.delayed(obj.mpid(), portal_name)
        self.cache.hset(cache_key, obj.typename(), mapping=obj.json())

    def get_stored_object(self, m_portal_id: str,
                          model_class: type[models.AbstractObject],
                          portal_name: str=None
                          ) -> type[models.AbstractObject]:
        """
            Returns body of stored object specified by model.
        """
        #: get mapping.
        cache_key = self.key_mgr.delayed(m_portal_id, portal_name)
        json = self.cache.hget(cache_key, model_class.typename())
        return model_class(**json)  # type: ignore
