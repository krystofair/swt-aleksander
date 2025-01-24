"""
    Services
    --------
    Celery's tasks as high level services. It worth to tell,
    that module has celery app configured so it is entry point
    for workers. Here has to be provided
"""
import logging

from .clustering import ClusterService, RedisCache
from .dblayer import DbMgr, models as dbmodels
from . import models, exc, processing
from .exc import ObjectAlreadyProcessed
from . import configs

import celery
from celery.app.log import Logging
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session
from celery import Task
import hydra


with hydra.initialize_config_dir(version_base=configs.VERSION_BASE, config_dir=configs.CONFIG_DIR_PATH):
    cfg = hydra.compose(config_name="redis")  # type: ignore

app = celery.Celery(task_cls='aleksander.services.Service', broker=f"redis://{cfg.broker.host}:{cfg.broker.port}/0")
log = Logging(app).get_default_logger()
log.setLevel(logging.DEBUG)

class Service(Task):
    """
        Base for service layer tasks.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with hydra.initialize_config_dir(version_base=configs.VERSION_BASE, config_dir=configs.CONFIG_DIR_PATH):
            use_database: str = hydra.compose(config_name="aleksander").get('db')

        self.db = DbMgr(use_database)
        redis = RedisCache()
        self.cluster = ClusterService(redis)


@app.task(bind=True)
def health_check(base: Service, url, body):
    print(url)
    print(body)
    with base.db.eng.connect() as connection:
        print(connection.info)
    return ":)"


@app.task(bind=True)
def saving_stored_stats(base: Service, match_id: models.MatchId, match_portal_id: str):
    """
        Gets stats json from cache and save it in db with match_id foreign key.
    """
    stats: models.Statistics = base.cluster.get_stored_object(match_portal_id, models.Statistics)  # type: ignore
    if not stats:
        return
    with Session(base.db.eng) as session:
        for stat in stats.data:
            session.add(dbmodels.Statistic(
                match_id = str(match_id),
                name = stat.name,
                home = stat.home,
                away = stat.away
            ))
        session.commit()
        base.cluster.sign_object_processed(match_id, stats.typename())
        log.info("Stats from cache migrated to database successfully.")


@app.task(bind=True)
def match_processing(base: Service, response_url, response_body):
    try:
        processor = processing.reg.select(response_url)
        if not processor:
            log.warning("Processor not found for url: '{url}'. All processors accessible: {ps}".format(
                url=response_url,
                ps=', '.join([str(t) for t in processing.reg.entries])
            ))
        try:
            match: models.Match = processor.task(response_url, response_body)
            log.debug(match.json())
            if not isinstance(match, models.Match):
                # TODO: inform administrator about errors in configuration somehow.
                raise ValueError("Here processor has to return Match model.")
            #: correlation section
            mid = match.match_id()
            mpid = match.mpid()
            log.debug(f"{mid=}, {mpid=}")
            base.cluster.map_match_id(mpid, mid)
            #: Find is there temporary object for me and plan tasks for saving it.
            for m in [models.Statistics, models.Object]:
                if (base.cluster.get_stored_object(mpid, m)
                        and not base.cluster.check_object_processed(mid, m.typename())):
                    match m.typename():
                        case "Statistics": saving_stored_stats.apply_async(args=(mid, mpid))
                        #: Add specific for others.
            if base.cluster.check_object_processed(mid, match.typename()):
                raise exc.MatchAlreadyProcessed(match_id=mid, match_portal_id=mpid, portal="sofascore")
        except exc.BuildModelException as e:
            log.error(e)
            return
        #: saving in database
        with Session(base.db.eng) as session:
            session.add(dbmodels.Match(
                match_id = str(match.match_id()),
                when = match.when,
                country = match.country,
                stadium = match.stadium,
                home = match.home,
                away = match.away,
                home_score = match.home_score,
                away_score = match.away_score,
                referee = match.referee,
                league = match.league,
                season = match.season
            ))
            session.commit()
            base.cluster.sign_object_processed(mid, match.typename())  # raise exception MatchAlreadyProcessed? example.

    except exc.MatchAlreadyProcessed as e:
        log.info(f"Match {e.match_id} (portal:{e.portal}) already processed")
    except DatabaseError as e:
        log.error(f"DatabaseError: {e}")
    except Exception as e:
        log.error(e)
    else:
        log.info('match processed correctly and saved in database')


@app.task(bind=True)
def statistics_processing(base: Service, response_url, response_body):
    processor = processing.reg.select(response_url)
    try:
        stats: models.Statistics = processor.task(response_url, response_body)
        match_id: models.MatchId = base.cluster.get_match_id(stats.mpid())
        db_stats = list()
        #: match_id is None means that match object not created yet.
        log.debug(f"{match_id=}")
        if match_id and base.cluster.check_object_processed(match_id, stats.typename()):
            raise ObjectAlreadyProcessed(stats.typename(), match_id)
        if not match_id:
            # save statistics only in cache.
            log.debug(stats)
            base.cluster.store_temporary(stats)
            log.info(f"Stored temporary obj: {stats.__class__}")
        else:
            for stat in stats.data:
                s = dbmodels.Statistic(
                    match_id = stats.mpid(),
                    name = stat.name,
                    home = stat.home,
                    away = stat.away
                )
                db_stats.append(s)
            #: saving in database
            with Session(base.db.eng) as session:
                session.add_all(db_stats)
                session.commit()
                base.cluster.sign_object_processed(match_id, stats.typename())
    except ObjectAlreadyProcessed as e:
        log.info(e)
    except DatabaseError as e:
        log.error(f"Statistics are not saved in database, because: {e}")
    except Exception as e:
        log.exception(e)
    else:
        log.info("Statistics processed successfully.")
