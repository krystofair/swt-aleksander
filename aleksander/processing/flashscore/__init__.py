"""
    Processing data from Flashscore statistics portal.
"""
import pathlib
import re
import operator
import itertools
import logging
from collections import deque
import copy

from aleksander import exc, configs
from aleksander.models import *
from aleksander.processing import reg
from aleksander.clustering import RedisCache
from aleksander.utils import dicts as dp
from .caching import FootballMatchBuilder
from . import frags, utils

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
    log.info("start match_t from flashscore")
    fragment = None
    try:
        parser, object_id = frags.pick_right_fragment_func(url)
        fragment = parser(object_id, body)
    except exc.BuildModelException as e:
        if e.field == 'scores':
            log.info("Exception handled, scores in this fragment were wrong,"
                     " wait for another fragment.")
            log.info(f"URL for what the fragment was wrong: {url}.")
            #: Fragment not cached, but error handled, so we don't pass this
            #  error further.
            raise exc.FragmentCached(portal='flashscore', fragment='DC_1',
                                     field='scores', prototype='')
        else:
            raise

    except Exception as e:
        log.exception(e)
        raise
    if fragment:
        log.info("Fragment parsed properly.")
        builder = FootballMatchBuilder(object_id, RedisCache())
        builder.add(fragment)
        builder.save()
        if builder.check_fragments():
            return builder.build()
        else:
            raise exc.FragmentCached(portal='flashscore', fragment=str(type(fragment)), field='', prototype=fragment)
    raise exc.ChangedPayloadException(portal='flashscore', body=body)


@reg(r"feed/df_st_1_([0-9a-zA-Z]+)/?$",  model=Statistics)
def stats_t(url, body):
    log.info("start stats_t from flashscore")
    event_portal_id = re.search(r"feed/df_st_1_([0-9a-zA-Z]+)/?$", url).group(1)
    stats = list()
    # processed_stats = set()
    parser = FootballStatParser(body)
    for stat in parser:
        #: here will be only stats to saved
        stats.append(Statistic(**stat))
        log.info("add stat: {}")
    statistics = Statistics(match_portal_id=event_portal_id, stats=stats)
    return statistics


class FootballStatParser:
    """
        Defines iterator protocol: __iter__, __next__. to be used as stats generator.
    """

    def __init__(self, body):
        """
            If you change amount of possible states,
            you should implement that you exactly now for what state
            you getting stats.
        """
        # ALL_STATES = ['match', '1st', '2nd', 'extra']
        self.POSSIBLE_STATES = ['match']
        self.state = None
        self.groups = utils.raw(body)
        self.eff_stats_delay_buffer = deque(maxlen=2)
        self.end = False
        """Once an iterator’s __next__() method raises StopIteration, it must continue to do so on subsequent calls.
        Implementations that do not obey this property are deemed broken."""

    def __iter__(self):
        return self

    def __next__(self):
        if self.end:
            raise StopIteration()
        if self.eff_stats_delay_buffer:
            return self.eff_stats_delay_buffer.pop()
        group = next(self.groups)
        try:
            match len(group):
                case 0:
                    #: The last group is always empty - after A1 with hash.
                    self.end = True
                    raise StopIteration()
                case 1:
                    if 'SE' in group:
                        self._change_state(group['SE'])
                        log.debug("Change state, new state is {}".format(self.state))
                    #: reccurent invoke my next method cause this would be return None,
                    #  which is not acceptable.
                    return self.__next__()
                #: Rest of case is treat as group of statistic.
                case _:
                    stat = self._process_stat(group)
                    stat_list = utils.try_split_stat_with_effectivity_form(stat)
                    stat_list_cleared = list(map(self._clear_stat, stat_list))
                    if len(stat_list_cleared) > 1:
                        self.eff_stats_delay_buffer.appendleft(stat_list_cleared[1])
                    return stat_list_cleared[0]
        except ValueError as e:
            log.error(f"Parsing failure with {e}")
            log.info("Statistics skipped.")
        raise ValueError('Returning None from FootballStatParser\'s __next__ method')
    
    def _change_state(self, new_state):
        #: Assign new_state to state if possible
        state = [s for s in self.POSSIBLE_STATES if s in new_state.lower()]
        if len(state) == 1:
            #: If possible new_state then set self.state as new.
            self.state = state.pop()
        else:  # another iteration where state was not possible
            hint = ""
            #: If self.state is still None, that first state wasn't as expected.
            if self.state is None:
                hint = " HINT: Is stats' order is correct?"
                raise ValueError(f"Impossible state.{hint}")
            #: If self.state did not changed to new_state then, this is over.
            elif self.state != new_state:
                self.end = True
                raise StopIteration()


    def _clear_stat(self, stat):
        stat['home'] = utils.to_float(stat['home'])
        stat['away'] = utils.to_float(stat['away'])
        return stat

    def _process_stat(self, stat):
        log.debug("_process_stat got {}".format(stat))
        names_code_map = {'SG': 'name', 'SH': 'home', 'SI': 'away'}
        new_stat = {}
        for code, value in stat.items():
            if code in names_code_map:
                if self.state is None:
                    raise ValueError("State is not defined")
                new_stat[names_code_map[code]] = value
        #: variable `code` will be last set from for, so when processing group
        #  with state to change, this will raise and not valid exception.
        if len(new_stat) < len(names_code_map):
            raise ValueError("Stat not fully processed.")
        return new_stat

