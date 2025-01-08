""" ... """
import hydra
from hydra.utils import instantiate
from omegaconf import OmegaConf

from . import configs


@hydra.main(version_base=configs.VERSION_BASE, config_path="configs", config_name="databases")
def main(cfg: configs.Config):
	co = OmegaConf.to_container(cfg)
	conn = instantiate(cfg.db)
	print(conn)
	print(co)
	print(f"{type(conn)=}")

if __name__ == "__main__":
	main()

