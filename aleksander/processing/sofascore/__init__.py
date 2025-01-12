"""
    Processing module for sofascore.com
"""
import json
import re
import pathlib
import os
import logging
logging.basicConfig()

from .. import reg
from aleksander import exc
from aleksander.models import *
from aleksander.utils import dicts as dp

import orjson as jsonlib

log = logging.getLogger("sofascore_processor")
log.setLevel(logging.DEBUG)
# maybe setting log level from config? # FEATURE

@reg("www.sofascore.com/api/v1/event/[0-9]+$", Match)
def match_t(url: str, body: str):
    filename = 'sofascore-event.json'
    path = pathlib.Path(os.path.dirname(__file__)).joinpath(pathlib.Path(filename))
    with open(path, 'r', encoding='utf-8') as file:
        template = jsonlib.loads(file.read())
    json_body = jsonlib.loads(body)
    #: Shortcutted Body.
    sb = dp.make_template_dict(json_body, template)
    if not dp.test_correctness(template, sb):
        log.info(str(sb))
        raise exc.ChangedPayloadException("sofascore.com")
    event = sb["event"]
    try:
        return Match(
            match_portal_id = event["id"],
            when = datetime.datetime.fromtimestamp(event["startTimestamp"]),
            country = event["uniqueTournament"]["category"]["name"],
            stadium = f'{event["venue"]["city"]["name"]}:{event["venue"]["name"]}',
            home = event["homeTeam"]["name"],
            home_score = event["homeScore"]["current"],
            away = event["awayTeam"]["name"],
            away_score = event["awayScore"]["current"],
            referee = event["referee"]["name"],
            league = event["uniqueTournament"]["name"]
        )
    except:
        raise exc.BuildModelException(portal="sofascore.com", prototype=jsonlib.dumps(event).decode('utf-8'))



@reg("www.sofascore.com/api/v1/event/[0-9]+/statistics$", Statistics)
def stats_t(url: str, body: str) -> Statistics:
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
        #     raise exc.ChangedPayloadException("sofascore.com")
        stats_list = sb["statistics"]
        stats_groups = [ s["groups"] for s in stats_list if s["period"] == "ALL" ].pop(0)
        stats = list()
        event_id = re.search("www.sofascore.com/api/v1/event/([0-9]+)/statistics$", url).group(1)
        log.debug("Found event id: {}.".format(event_id))
        for group in stats_groups:
            for stat in group['statisticsItems']:
                try:
                    s = Statistic(
                        name=stat["name"],
                        home=float(stat["home"]),
                        away=float(stat["away"])
                    )
                    stats.append(s)
                except ValueError:
                    s = Statistic(
                        name=stat["name"],
                        home=float(stat["home"].rstrip('%'))/100,
                        away=float(stat["away"].rstrip('%'))/100
                    )
                    stats.append(s)
                except:
                    log.error("Processing single stat failed.")
        return Statistics(event_id, stats)
    except KeyError:
        raise exc.ChangedPayloadException(portal="sofascore")
    except json.JSONDecodeError:
        log.error("Cannot process sofascore statistics responses as json.")
        log.error(body)
        raise exc.ChangedPayloadException(portal="sofascore")
    except Exception:
        raise exc.BuildModelException(portal="sofascore.com", prototype=jsonlib.dumps(sb).decode('utf-8'))
