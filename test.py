import datetime
import subprocess
import unittest
import logging
from pathlib import Path

from aleksander import dblayer, services, processing
from aleksander.clustering import RedisCache, ClusterService
from aleksander.models import Statistic, MatchId, Statistics, Match
from aleksander.processing import flashscore
from aleksander.processing.flashscore import raw


from omegaconf import OmegaConf
from sqlalchemy.orm import Session
import orjson as jsonlib


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('testing')

class RedisConfigurationTest(unittest.TestCase):
    def test_redis_configuration(self):
        """ ... """
        # configuration
        rc = RedisCache()
        assert rc.host == "127.0.0.1", rc.host
        assert rc.port == 6379


class ClusteringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cmdline = "podman run --rm -d -p 6379:6379 --name redis4test redis:latest"
        subprocess.run(cmdline.split(' '))

    @classmethod
    def tearDownClass(cls):
        cmdline = "podman stop redis4test"
        subprocess.run(cmdline.split(' '))

    def test_redis_connection(self):
        redis = RedisCache()
        redis.host = 'localhost'
        redis.port = 6379
        r = redis.instance()
        r.set('something', 'hahahaha')
        receive = r.get('something')  # .decode('utf-8') nie chce tak robic, TODO: implement automatic decoding.
        assert receive == b'hahahaha'


class TestDomain(unittest.TestCase):

    def test_statistic_model(self):
        stat = Statistic("nazwa", 1.0, 2.0)
        print(stat)
        # assert jsonlib.dumps(stat.json()) == {'away': 2.0, 'home': 1.0, 'name': 'nazwa'}
        stat2 = Statistic("Przydluga nazwa Ze spacjami", 1, 2)
        # working about slug converter
        assert stat2.name == 'przydluga-nazwa-ze-spacjami'
        # assert stat2.typename() == 'stat:przydluga-nazwa-ze-spacjami'
        stats = Statistics("mpid", [stat, stat2])
        assert stats.typename() == "Statistics"
        assert stats.mpid() == 'mpid'
        serialized_form = stats.json()
        sts2 = Statistics.fromjson(serialized_form)
        assert stats == sts2

    def test_match_model_json(self):
        m = Match(
            '123', "2024-03-04t20:45",
            'poland','narodowy','legia','lech', 1, 1, 'sedzia', 'ekstraklasa'
        )
        serialized = m.json()
        m2 = Match.fromjson(serialized)
        assert m == m2

    def test_processors_registry(self):
        # test is integrated with processing module test task
        registry = processing.reg
        entry = registry.select("https://test.org/match/1231231")
        assert entry is None
        entry = registry.select("https://9532d4f0-077e-4e57-97f1-6022ced75124/match/1231231")
        assert entry.model == processing.TestObj
        assert entry.task('message') == 'message'



class TestDatabaseConfiguration(unittest.TestCase):
    def test_loading_configuration(self):
        mgr = dblayer.DbMgr("sqlite")
        print(OmegaConf.to_yaml(mgr._cfg))

    def test_add_to_db(self):
        """Tests if """
        db_mgr = dblayer.DbMgr('postgresql')
        with Session(db_mgr.engine) as session:
            session.add(dblayer.models.Statistic(
                match_id="1",
                name='xdddd',
                home=123,
                away=321
            ))


class TestServiceLayer(unittest.TestCase):
    def setUp(self):
        # TODO: preparation test database for do it full automatically.
        pass

    def test_get_access_to_db(self):
        @services.app.task(bind=True)
        def example_task(base: services.Service):
            log.debug("start example task")
            try:
                m = dblayer.models.Match(when=datetime.datetime(2023, 8, 1, 18, 0),
                                         country="poland",
                                         stadium="narodowy",
                                         home='Polska',
                                         away="Szkocja",
                                         referee="sad man")
                with Session(base.db.eng) as session:
                    session.add(m)
                    session.commit()
            except Exception as e:
                return str(e)

            return 'koniec'

        result = example_task.apply()
        assert result.result == 'koniec'

    def test_get_access_to_cache(self):
        pass


class TestFlashProcessor(unittest.TestCase):
    def setUp(self):
        self.FLOWS_TO_TEST = Path('/d/swt001/flashflows/')
    
    def test_parse_raw_data_subst(self):
        flowpath = Path.joinpath(self.FLOWS_TO_TEST, 'substitutions.raw')
        with open(flowpath, 'r', encoding='utf-8') as f:
            raw_data = f.read()
        list_parsed = list(raw(raw_data))
        assert list_parsed[2].getall("IF") == ["Adebayo E.", "Brown J."], list_parsed[2]

    def test_get_data_from_dc_1_fragment(self):
        flowpath = Path.joinpath(self.FLOWS_TO_TEST, 'bodo-match-results.raw')
        with open(flowpath, 'r', encoding='utf-8') as f:
            raw_data = f.read()
        cache_mock = lambda: 42
        cache_mock.instance = lambda: 42
        builder = flashscore.FootballMatchBuilder('testowe_id', cache_mock)
        builder = flashscore.dc_1_fragment(builder, raw_data)
        assert builder is not None
        assert builder.fragments[0].when == datetime.datetime(2025, 2, 20, 18, 45), builder.fragments[0].when
        assert builder.fragments[0].away_score == 2, builder.fragments[0].away_score
        assert builder.fragments[0].home_score == 5, builder.fragments[0].home_score