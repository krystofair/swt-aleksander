import datetime
import subprocess
import unittest
import logging
log = logging.getLogger('testing')

from omegaconf import OmegaConf
from sqlalchemy.orm import Session

from aleksander import dblayer, services, processing
from aleksander.clustering import RedisCache, ClusterService
from aleksander.models import StrId, Statistic, MatchId, Statistics


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
        unittest.skip("redis is not connected right now")
        return
        redis = RedisCache().instance()
        redis.set('something', 'hahahaha')
        receive = redis.get('something')  # .decode('utf-8') nie chce tak robic, TODO: implement automatic decoding.
        assert receive == b'hahahaha'

    def test_cluster_service(self):
        redis = RedisCache()
        cd = ClusterService(redis)
        # match_id typed, but it is string for now anyway
        match_id = MatchId('match-id')
        cd.add_object_type_of_match('match-id', 'stats')
        assert cd.is_match_have_that_object(match_id, 'stats') == True, 'stats object not on list'
        assert cd.is_match_already_processed(match_id) == False, 'match was check as processed'
        cd.sign_match_as_processed(match_id)
        assert cd.is_match_already_processed(match_id) == True, 'match was not processed'


class TestDomain(unittest.TestCase):
    def test_StrId_descriptor(self):
        generated = StrId.gen_id()

        class T:
            identity = StrId(generated)

        t = T()
        assert t.identity == generated
        # changing type tu string, with encoding UTF8
        t.identity = b'nowa tozsamosc'
        assert t.identity == 'nowa tozsamosc'

    def test_StrId_as_non_descriptor(self):
        MyType = StrId
        match_id = MyType("problem")
        assert match_id == "problem"
        assert str(match_id) == "problem"

    def test_statistic_model(self):
        stat = Statistic("nazwa", 1.0, 2.0)
        print(stat)
        assert stat.json() == {'away': 2.0, 'home': 1.0, 'name': 'nazwa'}
        stat2 = Statistic("Przydluga nazwa Ze spacjami", 1, 2)
        # working about slug converter
        assert stat2.name == 'przydluga-nazwa-ze-spacjami'
        # assert stat2.typename() == 'stat:przydluga-nazwa-ze-spacjami'

        stats = Statistics("mpid", [stat, stat2])
        assert stats.typename() == "stats"
        assert stats.mpid() == 'mpid'
        assert stats.json() == {
            "_match_portal_id": "mpid",
            "_stats": [
            {"name": "nazwa", "home": 1.0, "away": 2.0},
            {"name": "przydluga-nazwa-ze-spacjami", "home": 1.0, "away": 2.0}
        ]}

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
