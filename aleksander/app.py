"""
    Objects for building flow in application.
"""

from typing import Any
import logging

import zmq
import celery

from . import configs
from .svclayer import service_layer_app as main_app

log = logging.getLogger("aleksander")


class ResponseService:
    @staticmethod
    def decode_message(response_body) -> tuple[Any, ...]:
        """
            Decodes messages for internal format.
        """
        log.info(f"--Receive message--\n{response_body}\n-----")
        return (1, 2, 3)

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

