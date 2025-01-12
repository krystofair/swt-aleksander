"""
    I didn't like explaining obvious things. :)
    But here you have classes for exceptions to do error handling in elegant way.
    For example, when something raise you only handle errors you know, others are probably BUGs. :)
    Btw exceptions should be like DomainEvents and contain only necessary information about error.
"""
from attrs import define

from . import models


@define
class ChangedPayloadException(Exception):
    """
        When some part of message body does not exist.
        This describes situation when probably there were changes in portal's api.
    """
    #: Which portal this occured?
    portal: str


@define
class BuildModelException(ChangedPayloadException):
    """
        Problem were there was last step of building model.
    """
    #: JSON from which model was trying to be built
    prototype: str


@define
class MatchAlreadyProcessed(Exception):
    """
        Match Already Processed so
    """
    match_id: models.MatchId
    match_portal_id: str
    portal: str


@define
class ObjectAlreadyProcessed(Exception):
    """
        Some object is already collected.
    """
    typename: models.ObjectType
    match_id: models.MatchId
