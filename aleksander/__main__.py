
import hydra
from hydra.utils import instantiate
from omegaconf import OmegaConf

from dblayer import config

@hydra.main(version_base=None, config_path="../configs", config_name='config')
def main(cfg: config.Config):
	co = OmegaConf.to_container(cfg)
	conn = instantiate(cfg.db)
	print(conn)
	print(co)
	print(f"{type(conn)=}")

if __name__ == "__main__":
	main()

