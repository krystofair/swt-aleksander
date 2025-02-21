"""
    Processing data from Flashscore statistics portal.
"""
import pathlib

from aleksander.models import *
from aleksander import reg, exc, configs
from aleksander.utils import dicts as dp

import orjson as jsonlib

log = configs.log


def log_big_messages(message, filename):
    with open()

def parse_raw_dc_1(url, body) -> Object:
    """This will raise FragmentCached, cause """

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