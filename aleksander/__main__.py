""" ... """
import logging
import asyncio
import sys

import hydra
import celery.exceptions as celery_exc
from omegaconf import OmegaConf
import zmq
import zmq.asyncio

from . import configs, services, app


#: Initialize hydra configuration globally here, because not work with asyncio.
with hydra.initialize(version_base=configs.VERSION_BASE, config_path="configs"):
	CONFIG: configs.MainConfig = hydra.compose(config_name="config")  # type: ignore

#: Initialize logging
logging.basicConfig()
#: Initialize logger
log = logging.getLogger("aleksander")
log.setLevel(configs.LOG_LEVEL)


async def main(cfg: configs.MainConfig):
	log.info(OmegaConf.to_yaml(cfg))
	zmq_ctx = zmq.asyncio.Context.instance()
	sockets = dict()
	for service in cfg.services:
		s: zmq.Socket = zmq_ctx.socket(zmq.SUB)
		s.connect(f"tcp://{cfg.publisher.host}:{cfg.publisher.port}")
		s.subscribe(service.topic)
		sockets[s] = service.name
		log.info(f"Set socket {s} to service name {sockets[s]}")
	while True:
		rs, ws, xs = zmq.select(rlist = list(sockets.keys()), wlist=[], xlist=[])
		try:
			for socket in rs:
				log.debug(f"Socket {socket} processing")
				task: services.Service = app.ResponseService.find_service(services.app, sockets[socket])
				log.debug(f"Task found: {task.name}")
				if task:
					msg = await socket.recv()
					log.debug(msg[:79])
					topic, url, body = app.ResponseService.decode_message(msg)
					if topic:
						str_body = body.decode('utf-8')
						str_url = url.decode('utf-8')
						_ = task.apply_async(args=(str_url, str_body))  # discard result, there is no backend for results.
						log.debug(f"Sent {url} to workers")
				else:
					# TODO: inform admin about wrong configuration somehow.
					log.error("Task cannot be find.")
		except celery_exc.InvalidTaskError as e:
			log.error(e)
		except Exception as e:
			*info, traceback = sys.exc_info()
			log.error(info)
			log.error(e.with_traceback(traceback))


if __name__ == "__main__":
	asyncio.run(main(CONFIG))

