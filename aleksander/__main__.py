"""
	Entry point to run aleksander.
	Commands:
	1. index
		Tool for loading identifiers of events to redis under "loaded" key.
		Goals:
			Indexing events not loaded during current processing in aleksander.
			Indexing events at new empty instance of REDIS.
	2. serve
		Subscriber of portier to spread data to parsing in celery workers.
		Goals:
			High Performance of processing bytes from Proxy(Socks5) HTTP streams.
"""
import logging
import asyncio
import sys
import os

import click
import hydra
import celery.exceptions as celery_exc
from omegaconf import OmegaConf
import zmq
import zmq.asyncio
import sqlalchemy as sa


@click.group()
@click.option('--config', help="aleksander config dir, can be set by environment variable too")
@click.pass_context
def cli(ctx, config: str):
	if config:
		os.environ['ALEKSANDER_CONFIG_DIR'] = config
	from . import configs
	with hydra.initialize_config_dir(version_base=configs.VERSION_BASE, config_dir=configs.CONFIG_DIR_PATH):
		cfg: configs.MainConfig = hydra.compose(config_name="aleksander")  # type: ignore
	ctx.ensure_object(dict)
	ctx.obj['conf'] = cfg

@cli.command()
@click.pass_context
def index(ctx):
	asyncio.run(_index(ctx.obj['conf']))

@cli.command()
@click.pass_context
def serve(ctx):
	asyncio.run(_serve(ctx.obj['conf']))

# TODO: Maybe add some parameters like league to index.
#       This could be interesting to not always index all, but only league I will browse for.
async def _index(cfg):
	from . import clustering
	from .models import Match
	from .dblayer import DbMgr
	# from .dblayer.models import Match
	log = logging.getLogger('aleksander.indexer')
	db_mgr = DbMgr(cfg.db)
	cache = clustering.ClusterService(clustering.RedisCache)
	query = sa.text("SELECT match_id FROM matches")
	with sa.orm.Session(db_mgr.eng) as s:
		event_ids = [ r._mapping['match_id'] for r in s.execute(query).all() ]
		with click.progressbar(event_ids) as bar:
			for id in bar:
				cache.sign_object_processed(id, Match.typename())


# async def main(cfg: configs.MainConfig):
async def _serve(cfg):
	from . import services, app
	log = logging.getLogger("aleksander")
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
					if topic and body.strip():
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
	cli()

