"""
    Services
    --------
    Celery's tasks as high level services.
"""

import logging
import sys

import celery
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session
from celery import Task
import hydra

from .clustering import ClusterService, RedisCache
from .dblayer import DbMgr, models as dbmodels
from . import models, exc
from .exc import ObjectAlreadyProcessed
from .processing import reg
from .configs import VERSION_BASE

app = celery.Celery(task_cls='aleksander.services.Service')

log = logging.getLogger("services")


class Service(Task):
    """
        Base for service layer tasks.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with hydra.initialize(version_base=VERSION_BASE, config_path='configs'):
            use_database: str = hydra.compose(config_name='config').get('db')

        self.db = DbMgr(use_database)
        self.cluster = ClusterService(RedisCache())


@app.task(bind=True)
def health_check(base: Service, url, body):
    print(url)
    print(body)
    with base.db.eng.connect() as connection:
        print(connection.info)
    return ":)"

@app.task(bind=True)
def match_processing(base: Service, response_url, response_body):
    try:
        processor = reg.select(response_url)
        try:
            match: models.Match = processor.task(response_url, response_body)
            if not isinstance(match, models.Match):
                # TODO: inform administrator about errors in configuration somehow.
                raise ValueError("Here processor has to return Match model.")
            #: correlation section
            mid = match.match_id()
            mpid = match.mpid()
            base.cluster.bind_match_portal_id_to_domain(mpid, mid)
            if base.cluster.is_match_already_processed(mid):
                raise exc.MatchAlreadyProcessed(match_id=mid, match_portal_id=mpid, portal="sofascore.com")
            base.cluster.sign_match_as_processed(mid)  # raise exception MatchAlreadyProcessed? example.
        except exc.BuildModelException as e:
            log.error(e)
            return
        except Exception as e:  # some errors when cache access?
            log.error(e)
            return

        #: saving in database
        with Session(base.db.eng) as session:
            session.add(dbmodels.Match(**match.json()))
            session.commit()
    except exc.MatchAlreadyProcessed as e:
        log.info(f"Match {e.match_id} (portal:{e.portal}) already processed")
    except DatabaseError as e:
        type, value, traceback = sys.exc_info()
        log.error(f"{type}, {value}")
        log.exception(e)

    except Exception as e:
        log.error(e)
    else:
        log.info('match processed correctly and saved in database')


@app.task(bind=True)
def statistics_processing(base: Service, response_url, response_body):
    ptask = reg.select(response_url)
    try:
        stats: models.Statistics = ptask.task(response_url, response_body)
        match_id: models.MatchId = base.cluster.match_portal_id_with_domain(stats.mpid())
        db_stats = list()
        statype = stats.typename()
        if base.cluster.is_match_have_that_object(match_id, statype):
            raise ObjectAlreadyProcessed(statype, match_id)
        for stat in stats.data:
            s = dbmodels.Statistic(
                match_id = stats.mpid(),  # TODO: prototype
                name = stat.name,
                home = stat.home,
                away = stat.away
            )
            db_stats.append(s)
            #: saving in database
            with Session(base.db.eng) as session:
                session.add_all(db_stats)
    except ObjectAlreadyProcessed as e:
        log.info(e)
    except Exception as e:
        log.exception(e)

    print("proces stats")
