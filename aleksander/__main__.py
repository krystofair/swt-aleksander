""" ... """
import hydra
from hydra.utils import instantiate
from omegaconf import OmegaConf

from . import configs


@hydra.main(version_base=configs.VERSION_BASE, config_path="configs", config_name="config")
def main(cfg: configs.MainConfig):
	print('dzien dobry')

if __name__ == "__main__":
	main()

