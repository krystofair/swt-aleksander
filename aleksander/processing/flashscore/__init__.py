"""
    Processing data from Flashscore statistics portal.
"""
import pathlib
import re
import operator
import itertools
import logging

from aleksander import exc, configs
from aleksander.models import *
from aleksander.processing import reg
from aleksander.clustering import RedisCache
from aleksander.utils import dicts as dp
from .caching import FootballMatchBuilder
from . import frags

import orjson as jsonlib
import multidict

log = logging.getLogger("FlashscoreProcessor")


@reg(r"www\.flashscore\.com/match/([0-9a-zA-Z]+)/?$", Match)
@reg(r"feed/dc_1_([0-9a-zA-Z]+)/?$", Match)
def match_t(url, body) -> Match:
    """
        This will raise FragmentCached, for inform that all goes successfully.
        Or return Match if all fragments are ready.
    """
    fragment = None
    try:
        object_id, parser = frags.pick_right_fragment_func(url)
        fragment = parser(object_id, body)
    except Exception as e:
        log.exception(e)
        raise

    if fragment:
        builder = FootballMatchBuilder(object_id, RedisCache())
        builder.add(fragment)
        builder.save()

        if builder.check_fragments():
            return builder.build()
        else:
            raise exc.FragmentCached(portal='flashscore', fragment=str(type(fragment)))
    raise ValueError("Something not going well.")

