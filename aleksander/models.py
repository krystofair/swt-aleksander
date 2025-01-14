import typing
import datetime
import uuid
import abc
import collections

import slugify
import attrs
from attrs import asdict, define, field
import orjson as jsonlib


unicode_slugify = slugify.slugify


class StrId(collections.UserString):
    """
        Descriptor class for treat Identity as str.
        But can be used as normal object as well for id saved in str.
    """
    def __init__(self, seq):
        #: Add bytes typing automatic decoding by utf-8.
        sq = seq
        if isinstance(seq, bytes):
            sq = seq.decode('utf-8')
        super().__init__(sq)

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        v = value
        if isinstance(value, bytes):
            v = value.decode('utf-8')
        instance.__dict__[self.name] = v

    def __get__(self, instance, owner):
        try:
            return instance.__dict__[self.name]
        except KeyError:
            return self.data

    def __bool__(self):
        return bool(self.data)

    @staticmethod
    def gen_id() -> str:
        return str(uuid.uuid4())


#: Type alias
MatchId = StrId

#: For now this is 'str' type, but should be as hierarchy of AbstractObject.
ObjectType = typing.NewType("ObjectType", str)


class AbstractObject(abc.ABC):

    #: Describes type of object this can be anything. TODO: build enum here.
    @staticmethod
    def typename() -> ObjectType:
        return ObjectType("object")

    def mpid(self) -> str:
        """Returns match portal identificator."""
        pass

    def json(self) -> dict:
        """Returns object in JSON"""
        pass


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

    @staticmethod
    def typename() -> ObjectType:
        return ObjectType('object')

    def json(self) -> dict:
        return jsonlib.loads(self.data)

    # this is
    # def match_id(self):
    #     return clustering.ClusterService.match_portal_id_with_domain(self.match_portal_id)



@define(frozen=True)
class Statistic:
    name = field(converter=unicode_slugify, type=str)
    home = field(type=float)
    away = field(type=float)

    def json(self) -> dict:
        """Returns self as json string"""
        return asdict(self)  # type: ignore

@define
class Statistics(AbstractObject):
    _match_portal_id = field(type=str)
    _stats = field(type=list[Statistic])

    @property
    def data(self):
        return self._stats

    def mpid(self):
        return self._match_portal_id

    @staticmethod
    def typename() -> ObjectType:
        return ObjectType(f"stats")

    def json(self):
        return asdict(self)

@define
class Match(AbstractMatch):
    match_portal_id = field(type=str)
    when = field(type=datetime.datetime)
    country = field(type=str, converter=unicode_slugify)
    stadium = field(type=str, converter=unicode_slugify)
    home = field(type=str, converter=unicode_slugify)
    away = field(type=str, converter=unicode_slugify)
    home_score = field(type=int)
    away_score = field(type=int)
    referee = field(type=str, converter=unicode_slugify)
    league= field(type=str, converter=unicode_slugify)

    @staticmethod
    def typename() -> ObjectType:
        return ObjectType('match')

    def mpid(self) -> str:
        return self.match_portal_id

    def json(self) -> dict:
        return asdict(self)

    def match_id(self) -> MatchId:
        """
            First implementation for match_id, here in the future can be some kind of vector.
            For easy search in vector database. XXX
        """
        # TODO: change for universal, this is only temporary solution, in constraint to using only one portal.
        return MatchId(self.match_portal_id)

