"""
    Processing data from Flashscore statistics portal.
"""

from ..models import *
from . import reg


@reg("www.flashscore.com/match/[0-9a-zA-Z]+/?$", Match)
def html_match(message) -> Match:
    return Match(**message)