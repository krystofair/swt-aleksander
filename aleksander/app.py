"""
    Objects for building flow in application.
"""
import logging

import zmq

from . import configs
from .services import app, Service


log = logging.getLogger("app")


class ResponseService:
    @staticmethod
    def decode_message(response_body: bytes) -> tuple[bytes, bytes, bytes]:
        """
            Decodes messages for internal format.
        """
        try:
            topic, rest = response_body.split(b"||", 1)
            url, body = rest.split(b"\r\n\r\n", 1)  # split by CRLFCRLF
            return topic, url, body
        except ValueError:
            log.error("Decoded message fail, maybe format changed?")
            return b'', b'', b''


    @staticmethod
    def find_service(self, name) -> Service | None:
        for taskname in app.tasks:
            if name in taskname:
                return app.tasks[taskname]
        return None
