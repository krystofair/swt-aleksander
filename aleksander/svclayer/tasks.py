"""
    Services
    --------
    Celery's tasks as high level services. This special celery app is defined
    in __init__ of this module.
"""
import models


@service_layer_app.task(base=models.Service)
def match_processing():
    print("process match")


@service_layer_app.task(base=models.Service)
def statistics_processing():
    print("proces stats")

