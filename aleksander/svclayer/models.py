"""
    Here are models for services layer. Specifically, a services.
"""

from celery import Task
import hydra

from ..clustering import ClusterService, RedisCache
from ..dblayer import DbMgr
from . import VERSION_BASE


class Service(Task):
    """
        Base for service layer tasks.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with hydra.initialize(version_base=VERSION_BASE, config_path='../configs'):
            use_database: str = hydra.compose(config_name='config').get('db')

        self.db = DbMgr(use_database)
        self.cluster = ClusterService(RedisCache())