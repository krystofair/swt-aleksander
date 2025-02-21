import logging
import pathlib
import os

import orjson as jsonlib
import multidict

from aleksander import exc

log = logging.getLogger(__name__)


def cut_json_from_html_fragment(body):
    templ_filename = "match-event.json"
    path = pathlib.Path(os.path.dirname(__file__)).joinpath(pathlib.Path(templ_filename))
    if 'window.environment' not in body:
        raise exc.BuildModelException(portal='flashscore', field='window.environment', prototype='Lack of variable from javascript script in html data.')
    var_idx = body.index('window.environment')
    try:
        rel_start_idx = body[var_idx:].index('{')
        rel_end_idx = body[var_idx:].index('};')
        json_payload = body[var_idx + rel_start_idx : var_idx + rel_end_idx + 1]
        log.debug(json_payload[:30])
        return jsonlib.loads(json_payload)
    except ValueError as e:
        if 'substring not found' in e:
            raise exc.BuildModelException(portal='flashscore', field='window.environment', prototype='Lack of variable from javascript script in html data.')
        log.exception(e)
    except jsonlib.JSONDecodeError as e:
        log.error(e)
    return None


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

