"""
    Services
    --------
    Celery's tasks as high level services. This special celery main_app is defined
    in __init__ of this module.
"""
from . import service_layer_app
from .models import Service
from aleksander.domain import Match


@service_layer_app.task(bind=True)
def match_processing(self: Service, response_url, response_body):
    # subtask = select_task(response_url)
    match: Match = (response_body)
    if self.cluster.is_match_already_processed(match.match_id()):
        return
    print("process match")


@service_layer_app.task(bind=True)
def statistics_processing(self):
    print("proces stats")

