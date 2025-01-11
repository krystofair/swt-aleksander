""" ... """
import logging
import asyncio

import hydra
from omegaconf import OmegaConf
import zmq
import zmq.asyncio

from . import configs, services, app


#: Initialize hydra configuration globally here, because not work with asyncio.
hydra.initialize(version_base=configs.VERSION_BASE, config_path="configs")
CONFIG: configs.MainConfig = hydra.compose(config_name="config")  # type: ignore

#: Initialize log
log = logging.getLogger("aleksander")
log.setLevel(logging.INFO)

async def main(cfg: configs.MainConfig):
	log.info(OmegaConf.to_yaml(cfg))
	zmq_ctx = zmq.asyncio.Context.instance()
	sockets = dict()
	for service in cfg.services:
		s: zmq.Socket = zmq_ctx.socket(zmq.SUB)
		s.subscribe(service.topic)
		sockets[s] = service.name
	while True:
		for sock in sockets.keys():
			msg = await sock.recv_multipart()
			if msg:
				task: services.Service = app.ResponseService.get_task(services.app, sockets[sock])
				if task:
					_, url, body = app.ResponseService.decode_message(msg)
					task.apply_async(url, body)
				else:
					# TODO: inform admin about wrong configuration somehow.
					log.error("Task cannot be find.")


if __name__ == "__main__":
	asyncio.run(main(CONFIG))

