"""
    Services
    --------
    Celery's tasks as high level services.
"""

import logging

import celery
from sqlalchemy.orm import Session
from celery import Task
import hydra

from .clustering import ClusterService, RedisCache
from .dblayer import DbMgr
from . import models as dmodels
from .models import AbstractObject
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
def match_processing(base: Service, response_url, response_body):
    try:
        subtask_procesor = reg.select(response_url)
        match: dmodels.Match = subtask_procesor.task(response_body)
        if not isinstance(match, dmodels.Match):
            # TODO: inform administrator about errors in configuration somehow.
            raise ValueError("Here processor has to return Match model.")
        #: correlation section
        mid = match.match_id()
        if base.cluster.is_match_already_processed(mid):
            log.info(f"Match with {mid} already processed.")
            return

        #: saving in database
        with Session(base.db.eng) as session:
            session.add(match)
            session.commit()
    except Exception as e:
        log.error(e)
    else:
        log.info('match processed correctly and saved in database')


@app.task(bind=True)
def statistics_processing(base: Service, response_url, response_body):
    ptask = reg.select(response_url)
    stat: dmodels.Statistic = ptask.task(response_body)
    match_id: dmodels.MatchId = base.cluster.match_portal_id_with_domain(stat.mpid())
    # I do this, because I don't like more that once calculation.
    # That is why this should be @property, but something not worked me in this abstration.
    statype = stat.typename()
    if base.cluster.is_match_have_that_object(match_id, statype):
        log.info(f"Object {statype} is already processed for {match_id}")
        return

    print("proces stats")
