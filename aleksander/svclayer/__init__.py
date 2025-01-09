import celery

from .tasks import *
from .models import Service

VERSION_BASE = "1.1"
service_layer_app = celery.Celery(task_cls='aleksander.svclayer.models.Service')