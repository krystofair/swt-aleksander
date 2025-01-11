"""
    Objects for building flow in application.
"""
import typing
from typing import Any
import logging

import zmq
import celery

from . import configs
from . import models as dmodels
from .services import app, Service

log = logging.getLogger("aleksander")

class ServiceRepository:
    """
        Here will have reversed dict.
    """


class ResponseService:
    @staticmethod
    def decode_message(response_body) -> tuple[Any, ...]:
        """
            Decodes messages for internal format.
        """
        log.info(f"--Receive message--\n{response_body}\n-----")
        return (1, 2, 3)
    @staticmethod
    def get_task(self, name) -> Service|None:
        for task in app.tasks:
            if name in task.name:
                return task
        return None

class SubscriberService:
    @staticmethod
    def create_sockets(topics: list[str]) -> list[zmq.Socket]:
        sockets = []
        ctx = zmq.Context.instance()
        for t in topics:
            s: zmq.Socket = ctx.socket(zmq.SUB)
            s.subscribe(t)
            sockets.append(s)
        return sockets

