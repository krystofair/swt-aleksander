import datetime
import unittest
import subprocess

from aleksander.clustering import RedisCache, ClusterService
from aleksander.domain import StrId, Statistic, MatchId
from aleksander import configs, dblayer

from omegaconf import OmegaConf
import hydra
from hydra import conf


class RedisConfigurationTest(unittest.TestCase):
    def test_redis_configuration(self):
        """ ... """
        # configuration
        rc = RedisCache()
        assert rc.config.cache.host == "127.0.0.1", rc.config.cache.host
        assert rc.config.cache.port == 6379

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

    def test_statistic_model(self):
        stat = Statistic("mpid", "nazwa", 1.0, 2.0)
        print(stat)
        assert stat.json() == str({"match_portal_id": "mpid",
                                   "name": "nazwa",
                                   "home": 1.0, "away": 2.0})
        stat2 = Statistic("mpid2", "Przydluga nazwa Ze spacjami", 1, 2)
        # working about slug converter
        assert stat2.name == 'przydluga-nazwa-ze-spacjami'
        assert stat2.typename() == 'Stat:przydluga-nazwa-ze-spacjami'

class TestDatabaseConfiguration(unittest.TestCase):
    def test_loading_configuration(self):
        mgr = dblayer.DbMgr("sqlite")
        print(OmegaConf.to_yaml(mgr._cfg))


class TestServiceLayer(unittest.TestCase):
    def setUp(self):
        # create test database
        # run docker with redis cache.
        pass

    def test_get_access_to_db(self):
        from aleksander.svclayer import service_layer_app, Service
        from aleksander.dblayer.models import Match
        @service_layer_app.task(bind=True)
        def test_task(base: Service):
            m = Match(when=datetime.datetime(2023,8,1,18,0),
                      country="poland",
                      stadium="narodowy",
                      home='Polska',
                      away="Szkocja",
                      referee="sad man")
            with base.db.engine().connect().begin() as transaction:

                transaction.commit()

            print('test')
        test_task.apply_local()

    def test_get_access_to_cache(self):
        pass

