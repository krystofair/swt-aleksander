import copy
import itertools
import typing
import datetime

from aleksander import clustering, models
from aleksander.models import unicode_slugify
from aleksander.utils import converters, validators

import redis
import orjson as jsonlib
from attrs import define, field, asdict

class FragmentsKeysMgr(clustering.CacheKeysMgr):
    """Inherit from CacheKeyMgr, to sign that logic is similar"""
    keys = {
        'fragment': "FRAGMENT({frag_nr},{object_portal_id},{typename})",
        'collection': "FRAG_COLLECTION({object_portal_id},{typename}})"
    }

    def __init__(self, obj_portal_id, obj_type):
        self.obj_id = obj_portal_id
        self.obj_type = obj_type

    def fragment(self, nr):
        return self._key(self.keys['fragment'].format(
            frag_nr=nr,
            object_portal_id=self.obj_id,
            typename=self.obj_type
        ))

    def collection(self):
        return self._key(self.keys['collection'].format(
            object_portal_id=self.obj_id,
            typename=self.obj_type
        ))


class FootballMatchFragments:
    
    TYPENAME = models.Match.typename()

    FRAGMENT_CLASS = {
        "NR": -1,  # index of fragment
        "DATA": ""  # data as in models.Object(AbstractObject) (JSON string)
    }

    @define
    class HtmlHash:
        #: Must be in all fragments
        match_portal_id = field(type=str)
        country = field(type=str, converter=unicode_slugify)
        # stadium = field(type=str, converter=unicode_slugify)
        home = field(type=str, converter=unicode_slugify)
        away = field(type=str, converter=unicode_slugify)
        league = field(type=str, converter=unicode_slugify)
        #: Trzeba będzie wyciągac sezon z daty. - napisac sobie taki utils.
        #season = field(type=str, validator=validators.match_season_format)

    @define
    class DC_1:
        match_portal_id = field(type=str)
        when = field(type=datetime.datetime, converter=converters.read_datetime)
        home_score = field(type=int)
        away_score = field(type=int)
    
    FRAGMENTS = [
        HtmlHash,
        DC_1
    ]

    @classmethod
    def new(cls, frag):
        try:
            nr = list(map(lambda x: isinstance(frag_data, x), cls.FRAGMENTS)).index(True) + 1
        except ValueError:
            raise TypeError(f"Cannot create FRAGMENT_CLASS from {type(frag)}({frag}).")
        frag_dict = asdict(frag)
        str_data = jsonlib.dumps(frag_dict)
        return {
            "NR": nr,
            "DATA": str_data
        }
    
    @classmethod
    def cache_fragment(cls, fragment, cache: redis.Redis):
        """
            This cached fragment and set 1 (as True) in collection list in cache.
        """
        key_mgr = FragmentsKeysMgr(fragment.match_portal_id, cls.TYPENAME)
        frag_dict = cls.new(fragment)
        nr = frag_dict['NR']
        cache.set(key_mgr.fragment(nr), frag_dict["DATA"])
        cache.hsetnx(key_mgr.collection(), nr, 1)


class FootballMatchBuilder:
    """
        self.fragments: list of objects `fragments_class` could be collected one by one in builder.
        frag_collections: list [True, False, ...] about indicator of fragment is loaded to builder or cache,
                          so that `frag_colls` could be saved in cache as another instance to easy check how
                          many fragments is lacking.
    """
    
    def __init__(self, match_portal_id, cache):
        self.key_mgr = FragmentsKeysMgr(match_portal_id, models.Match.typename())
        self.cache = self.C = cache.instance()
        self.match_portal_id = match_portal_id
        self.fragments = list()

    def add(self, fragment):
        if isinstance(fragment, tuple(FootballMatchFragments.FRAGMENTS)):
            self.fragments.append(fragment)
        else:
            raise TypeError("You r idiot or what? xD")

    @classmethod
    def collect(self):
        """
            Collect stored fragments in (REDIS) cache.
        """
        count_fragments = len(FootballMatchFragments.FRAGMENTS)
        collection_key = self.key_mgr.collection()
        keys = [self.key_mgr.fragment(nr)
                for nr in range(1, count_fragments+1)]
        return [ {"NR": nr+1, "DATA": self.cache.get(key)}
                 for nr, key in enumerate(keys)
                 if self.cache.hget(collection_key, nr+1) ]

    def check_fragments(self):
        """Check if we have enough fragments in cache to create match instance."""
        for i in range(1, len(FootballMatchFragments.FRAGMENTS)+1):
            key = self.key_mgr.collection()
            if not self.cache.hget(key, i):
                log.debug(f"Not found fragment nr {i}")
                break
        else:
            return True
        return False

    def save(self):
        for f in self.fragments:
            nr, _ = FootballMatchFragments.new(f)
            if self.cache.hget(self.key_mgr.collection(), nr):
                FootballMatchFragments.cache_fragment(f, self.cache)
    
    def delete(self):
        """Remove from cache all fragments and collection."""
        count_fragments = len(FootballMatchFragments.FRAGMENTS)
        collection_key = self.key_mgr.collection()
        keys = [self.key_mgr.fragment(r) for r in range(1, count_fragments+1)]
        self.cache.delete(*keys)
        self.cache.hdel(collection_key, *range(1, len(keys)+1))

    def build():
        match = {}
        try:
            for frag_dict in sorted(self.collect(), key=lambda x: x['NR']):
                py_obj = {}
                _, data = frag_dict.values()
                py_obj = jsonlib.loads(data)
                match |= py_obj
        except Exception as e:
            log.exception(e)
            raise
        return Match(**match, season="??", stadium="??", referee="??")
