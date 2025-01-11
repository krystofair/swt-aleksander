import typing
import datetime
import uuid
import abc

import slugify
from attrs import asdict, define, field


unicode_slugify = slugify.slugify


class StrId:
    """
        Descriptor class for treat Identity as str.
        But can be used as normal object as well for id saved in str.
    """
    def __init__(self, id: str|bytes):
        self.id = id
        if isinstance(id, bytes):
            self.id = id.decode('utf-8')

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
            return self.id

    def __str__(self):
        return self.id

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            if isinstance(other, str):
                return self.id == other
            else:
                raise

    @staticmethod
    def gen_id() -> str:
        return str(uuid.uuid4())


#: Type alias
MatchId = StrId

#: For now this is 'str' type, but should be enum.
ObjectType = typing.NewType("ObjectType", str)


class AbstractObject(abc.ABC):

    #: Describes type of object this can be anything. TODO: build enum here.
    def typename(self) -> ObjectType:
        return ObjectType("object")

    def mpid(self) -> str:
        """Returns match portal identificator."""
        pass

    def json(self) -> str:
        """Returns object in JSON"""
        pass


class AbstractMatch(AbstractObject):
    def match_id(self) -> MatchId:
        pass

@define
class Object(AbstractObject):
    #: event id
    match_portal_id: str

    #: Stores JSON in string
    data: str

    def mpid(self) -> str:
        return self.match_portal_id

    def typename(self) -> ObjectType:
        return ObjectType('object')

    def json(self) -> str:
        return self.data

    # this is
    # def match_id(self):
    #     return clustering.ClusterService.match_portal_id_with_domain(self.match_portal_id)



@define(frozen=True)
class Statistic(AbstractObject):
    match_portal_id = field(type=str)
    name = field(converter=unicode_slugify, type=str)
    home = field(type=float)
    away = field(type=float)

    def mpid(self) -> str:
        return self.match_portal_id

    @classmethod
    def loads(cls, json_data):
        """Build this class from json"""
        return cls()

    def typename(self) -> ObjectType:
        return ObjectType(f"stat:{self.name}")

    def json(self) -> str:
        """Returns self as json string"""
        return str(asdict(self))


@define
class Match(AbstractMatch):
    match_portal_id = field(type=str)
    when: datetime.datetime
    country = field(type=str, converter=unicode_slugify)
    stadium = field(type=str, converter=unicode_slugify)
    home = field(type=str, converter=unicode_slugify)
    away = field(type=str, converter=unicode_slugify)
    referee = field(type=str, converter=unicode_slugify)
    league= field(type=str, converter=unicode_slugify)

    def json(self) -> str:
        """Returns fields in json format."""
        return str(asdict(self))

    def __str__(self):
        return self.json()

    def match_id(self) -> MatchId:
        """
            First implementation for match_id, here in the future can be some kind of vector.
            For easy search in vector database. XXX
        """
        # TODO: change for universal, this is only temporary solution, in constraint to using only one portal.
        return MatchId(self.match_portal_id)

