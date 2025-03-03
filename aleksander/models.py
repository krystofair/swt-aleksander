import typing
import datetime
import abc
import logging

from aleksander import utils
from aleksander.utils import converters, validators

import slugify
import attrs
from attrs import asdict, define, field
import orjson as jsonlib


unicode_slugify = slugify.slugify
log = logging.getLogger("domain.model")

#: Type alias
MatchId = typing.NewType("MatchId", str)

#: For now this is 'str' type, but should be as hierarchy of AbstractObject.
ObjectType = typing.NewType("ObjectType", str)


class AbstractObject(abc.ABC):

    @classmethod
    def typename(cls) -> ObjectType:
        return ObjectType(cls.__name__)

    def mpid(self) -> str:
        """Returns match portal identity."""
        pass

    def todict(self):
        """
            Default implementation use `asdict` from `attrs` library.
            One exception is this abstract class, which is not `AttrsInstance` defined by `attrs.define`.
        """
        return asdict(self)

    def json(self) -> bytes:
        """Returns object in JSON"""
        return jsonlib.dumps(self.todict())

    @classmethod
    def fromjson(cls, data: bytes|str) -> type:
        """Build class from json."""
        dictionary = jsonlib.loads(data)
        return cls.fromdict(dictionary)

    @classmethod
    def fromdict(cls, dictionary) -> type:
        if not isinstance(dictionary, typing.Mapping):
            raise TypeError(f"Cannot build class by `fromdict` method when type is {dictionary.__class__!r}")
        try:
            log.info("Try build class {cls.__name__!r} by **dictionary style.")
            return cls(**dictionary)
        except:
            log.info("Generic method failed.")
            return None


class AbstractMatch(AbstractObject):
    def match_id(self) -> MatchId:
        pass

@define
class Object(AbstractObject):
    #: event id
    _match_portal_id: str

    #: Stores JSON in string
    data: str

    def mpid(self) -> str:
        return self._match_portal_id

    def todict(self):
        return {"data": self.data}

    @classmethod
    def fromdict(cls, dictionary) -> type:
        return super().fromdict(dictionary)


@define(frozen=True)
class Statistic:
    """
        Class is not AbstractObject in sense of domain model.
        This is Value Object for aggregated type Statistics.
    """
    name = field(converter=unicode_slugify, type=str)
    home = field(type=float)
    away = field(type=float)


@define
class Statistics(AbstractObject):
    _match_portal_id = field(type=str)
    _stats = field(type=list[Statistic])

    @property
    def data(self):
        return self._stats

    def mpid(self):
        return self._match_portal_id

    def todict(self):
        return {
            "match_portal_id": self._match_portal_id,
            "stats": [ asdict(stat) for stat in self._stats ]
        }

    @classmethod
    def fromdict(cls, dictionary) -> type:
        mpid = dictionary['match_portal_id']
        stats = [Statistic(**s) for s in dictionary['stats']]
        datad = {'match_portal_id': mpid, 'stats': stats}
        return super().fromdict(datad)

    def json(self) -> bytes:
        return jsonlib.dumps(self.todict())

    @classmethod
    def fromjson(cls, string) -> type:
        dictionary = jsonlib.loads(string)
        return cls.fromdict(dictionary)

@define
class Match(AbstractMatch):
    match_portal_id = field(type=str)
    when = field(type=datetime.datetime,
                 converter=converters.read_datetime,
                 validator=validators.now_is_after_3h_since_it)
    country = field(type=str, converter=unicode_slugify)
    stadium = field(type=str, converter=unicode_slugify)
    home = field(type=str, converter=unicode_slugify)
    away = field(type=str, converter=unicode_slugify)
    home_score = field(type=int)
    away_score = field(type=int)
    referee = field(type=str, converter=unicode_slugify)
    league= field(type=str, converter=unicode_slugify)
    season = field(type=str, validator=validators.match_season_format)

    def mpid(self) -> str:
        return self.match_portal_id

    def json(self) -> bytes:
        return jsonlib.dumps(self.todict())

    @classmethod
    def fromjson(cls, string) -> type:
        dictionary = jsonlib.loads(string)
        return super().fromdict(dictionary)

    def match_id(self) -> MatchId:
        """
            First implementation for match_id, here in the future can be some kind of vector.
            For easy search in vector database. XXX
        """
        # TODO: change for universal, this is only temporary solution, in constraint to using only one portal.
        return MatchId(self.match_portal_id)

