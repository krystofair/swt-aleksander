import logging
import re

from aleksander import exc
import aleksander.processing.flashscore.utils as utils
from aleksander.processing.flashscore.caching import FootballMatchFragments as FMF
from aleksander.processing.flashscore import regexes



log = logging.getLogger(__name__)


def pick_right_fragment_func(url):
    """
        Returns fragment_parser_func with event_id/object_id in tuple.
    """
    func_regex = [
        (html_fragment, regexes.MATCH_HTML_FRAGMENT_REGEX),
        (dc_1_fragment, regexes.DC_FRAGMENT_REGEX)
    ]
    for func, regex in func_regex:
        if m := re.search(regex, url):
            # return (m.group(1), func)
            return (func, m.group(1))
    log.warning("Not found right fragment function to process data.")
    return None


def dc_1_fragment(object_portal_id: str, body: str):
    """
        Parse dc_1 fragment. Get builder from outside and return it afterwards,
        but it is not necessary - builder is mutable object.
    """
    parts = {
        "when": "DC",
        "home_score": "DE",
        "away_score": "DF"
    }
    fragment = None
    frag_dict = {'match_portal_id': object_portal_id}
    try:
        for i, group in enumerate(utils.raw(body)):
            if i > 0:
                log.info("Dont parse more groups in DC_1 fragment.")
                break #: Dont want more groups
            for field, key in parts.items():
                frag_dict.update({field: group.get(key)})
        # XXX season wasn't find yet in analysis of streams from portal
        fragment = FMF.DC_1(**frag_dict, season="00/00")
        fragment.season=str(fragment.when.year)
        #: validation
        if not fragment.home_score or not fragment.away_score:
            raise ValueError("scores")
    except (ValueError, KeyError) as e:
        if "scores" in str(e):
            raise exc.BuildModelException(portal='flashscore', field='scores',
                                          prototype=str(frag_dict)) from None
        else:
            log.exception(e)
            raise
    except Exception as e:
        log.exception(e)
        raise exc.ChangedPayloadException(portal='flashscore', body=body)
    return fragment


def html_fragment(object_portal_id: str, body: str):
    py_obj = utils.cut_json_from_html_fragment(body)
    fragment = None
    try:
        if object_portal_id != py_obj['event_id_c']:
            raise exc.BuildModelException(portal='flashscore', field='event_id_c', prototype='An event_id is diffrent than passed.')
        match = {
            "match_portal_id": py_obj['event_id_c'],
            "home": py_obj['participantsData']['home'][0]['name'],
            "away": py_obj['participantsData']['away'][0]['name'],
            "country": py_obj['header']['tournament']['category'],
            "league": py_obj['header']['tournament']['tournament']
        }
        fragment = FMF.HtmlHash(**match)
    except ValueError as e:
        log.error(e)
    except KeyError as e:
        log.error(e)
        raise exc.ChangedPayloadException('flashscore', body=str(py_obj))
    return fragment
