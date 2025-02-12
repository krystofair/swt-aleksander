"""
    Processing module for sofascore.com
"""
import re
import pathlib
import os
import logging
logging.basicConfig()

from aleksander.processing import reg
from aleksander import exc
from aleksander.models import *
from aleksander.utils import dicts as dp

import orjson as jsonlib

log = logging.getLogger("sofascore_processor")
log.setLevel(logging.DEBUG)


@reg(pattern="www.sofascore.com/api/v1/event/[0-9]+$", model=Match)
def match_t(url: str, body: str):
    filename = 'sofascore-event.json'
    path = pathlib.Path(os.path.dirname(__file__)).joinpath(pathlib.Path(filename))
    with open(path, 'r', encoding='utf-8') as file:
        template = jsonlib.loads(file.read())
    try:
        json_body = jsonlib.loads(body)
        #: Shortcutted Body.
        sb = dp.make_template_dict(json_body, template)
        if not dp.test_correctness(template, sb):
            log.info(str(sb))
            raise exc.ChangedPayloadException(portal="sofascore", body=body)
    except jsonlib.JSONDecodeError:
        raise exc.ChangedPayloadException(portal="sofascore", body=body)
    event = sb["event"]
    try:
        #: pre initialize when field.
        pre_when = datetime.datetime.fromtimestamp(event["startTimestamp"])
        return Match(
            match_portal_id = event["id"],
            when = pre_when,
            country = event["tournament"]["category"]["name"],
            stadium = f'{event["venue"]["city"]["name"]}:{event["venue"]["name"]}',
            home = event["homeTeam"]["name"],
            home_score = event["homeScore"]["current"],
            away = event["awayTeam"]["name"],
            away_score = event["awayScore"]["current"],
            referee = event["referee"]["name"],
            league = event["tournament"]["name"],
            season = event['season']['year'] if 'season' in event and 'year' in event['season'] else str(pre_when.year)
        )
    except KeyError as e:
        if 'current' in str(e):
            log.info("Planned matches are not processing.")
        else:
            log.error(e)
            raise exc.ChangedPayloadException(portal="sofascore", body=body)
    except ValueError as e:
        log.error(e)
        raise exc.BuildModelException(portal="sofascore", field='unknown', prototype=jsonlib.dumps(event).decode('utf-8'))


@reg(pattern="www.sofascore.com/api/v1/event/[0-9]+/statistics$", model=Statistics)
def stats_t(url: str, body: str) -> Statistics|None:
    filename = 'sofascore-stats.json'
    path = pathlib.Path(os.path.dirname(__file__)).joinpath(pathlib.Path(filename))
    with open(path, 'r', encoding='utf-8') as file:
        template = jsonlib.loads(file.read())
    try:
        json_body = jsonlib.loads(body)
        #: Shortcutted Body.
        sb = dp.make_template_dict(json_body, template)
        # if not dp.test_correctness(template, sb):
        #     log.info(str(sb))
        #     raise exc.ChangedPayloadException("sofascore", body)
        stats_list = sb["statistics"]
        stats_groups = [ s["groups"] for s in stats_list if s["period"] == "ALL" ].pop(0)
        stats = list()
        event_id = re.search("www.sofascore.com/api/v1/event/([0-9]+)/statistics$", url).group(1)
        log.debug("Found event id: {}.".format(event_id))
        for group in stats_groups:
            for stat in group['statisticsItems']:
                try:
                    home_value = float(stat['home'])
                    away_value = float(stat['away'])
                    s = Statistic(
                        name=stat["name"],
                        home=home_value,
                        away=away_value
                    )
                    stats.append(s)
                except ValueError:
                    try:
                        regex = r"^\d+%?$|^\d+$|\d+?/\d+"
                        home_searches = [match.group() for match in re.finditer(regex, stat['home'], 0)]
                        away_searches = [match.group() for match in re.finditer(regex, stat['away'], 0)]
                        home_searches.sort(key=lambda x: len(x), reverse=True)
                        away_searches.sort(key=lambda x: len(x), reverse=True)
                        def get_value(x):
                            if '%' in x:
                                return float(x.rstrip('%')) / 100
                            elif '/' in x:
                                a, b = x.split('/', 1)
                                return float(a) / float(b)
                            else:
                                return float(x)
                        home_value = get_value(home_searches[0])
                        away_value = get_value(away_searches[0])
                        s = Statistic(
                            name=stat["name"],
                            home=home_value,
                            away=away_value
                        )
                        stats.append(s)
                    except Exception as e:
                        log.error("Cannot parse statistic in implemented ways. Skiped: {}, Error: {}".format(
                            stat['name'], e))
        return Statistics(event_id, stats)
    except KeyError:
        raise exc.ChangedPayloadException(portal="sofascore", body=body)
    except jsonlib.JSONDecodeError:
        log.error("Cannot process sofascore statistics responses as json.")
        log.error(body)
        raise exc.ChangedPayloadException(portal="sofascore", body=body)
    except Exception:
        raise exc.BuildModelException(portal="sofascore.com", field='unknown',
                                      prototype=jsonlib.dumps(sb, option=jsonlib.OPT_INDENT_2).decode('utf-8'))
