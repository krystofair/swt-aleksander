"""
    Processing data from Flashscore statistics portal.
"""
import pathlib
import re
import operator
import itertools

from aleksander import exc, configs
from aleksander.models import *
from aleksander.processing import reg
from aleksander.clustering import RedisCache
from aleksander.utils import dicts as dp
from .caching import (
    FootballMatchFragments as FMF,
    FootballMatchBuilder
)

import orjson as jsonlib
import multidict

log = configs.log

def raw(data):
    log.debug(data)
    groups = data.split('~')
    log.debug(groups[-5:])
    for group in groups:
        md = multidict.MultiDict()
        # In parts keys are doubled
        parts = group.split('¬')
        log.debug(parts[-5:])
        for part in parts:
            log.debug(part)
            if not part:
                continue
            key, value = part.split('÷')
            md.extend({key: value})
        #: yielding groups
        yield md


def dc_1_fragment(builder, body):
    """
        Parse dc_1 fragment. Get builder from outside and return it afterwards,
        but it is not necessary - builder is mutable object.
    """
    parts = {
        "when": "DC",
        "home_score": "DE",
        "away_score": "DF"
    }
    try:
        frag_dict = {}
        for i, group in enumerate(raw(body)):
            if i > 0:
                log.info("There were more groups. Next would be {}".format(group))
                break #: Dont want more groups
            for field, key in parts.items():
                frag_dict.update({field: group.get(key)})
        fragment = FMF.DC_1(**frag_dict)
        builder.add(fragment)
    except (ValueError, KeyError) as e:
        log.error(e)
    except Exception as e:
        log.exception(e)
        raise exc.ChangedPayloadException(portal='flashscore', body=body)
    finally:
        return builder

def parsing_all() -> Match:
    """
        This will raise FragmentCached, for inform that all goes successfully.
        Or return Match if all fragments are ready.
    """
    object_id = re.search(r"/feed/dc_1_(.*$)", url).group(1)
    builder = FootballMatchBuilder(object_id, RedisCache())
    raise exc.FragmentCached("DC_1 (when, scores) saved.")

@reg("www.flashscore.com/match/[0-9a-zA-Z]+/?$", Match)
def html_fragment(url: str, body: str) -> Match:
    templ_filename = "match-event.json"
    path = pathlib.Path(os.path.dirname(__file__)).joinpath(pathlib.Path(templ_filename))
    try:
        ## FIND SCRIPT TAG
        start, stop = "<scrip", "</scrip"
        startI = body.index(start)
        stopI = body[startI:].index(stop) + startI
        script = body[startI+6 : stopI]
        ##### EXTRACT JSON FROM VARIABLE ###
        #: New names for variables because of type change.
        startI = script.index("= {")
        stopI = script.rindex("};")
        json_body = script[startI+2:stopI]
        temp_dict_obj = jsonlib.loads(json_body)
        with open(path, 'r', encoding='utf-8') as template_file:
            template = jsonlib.loads(template_file.read())
        py_obj = dp.make_template_dict(temp_dict_obj, template)
    except ValueError as e:
        log.error(e)
        raise exc.ChangedPayloadException(portal='flashscore', body=body)
    except jsonlib.JSONDecodeError as e:
        log.error(e)
        raise exc.ChangedPayloadException(portal='flashscore', body=json_body)
    #: Here we have parsed Python Object `py_obj`
    if py_obj.get('event_info', {}).get('hasStats', None) is None:
        raise FeatureNotImplemented(feature="future events",
                                    message="Find future match in flashscore.")
    teams_data = py_obj.get('')
    #: json_body further processing.
    try:
        pass
    except ValueError as e:
        log.error(e)

    return Match(**message)