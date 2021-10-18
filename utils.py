import logging
from pathlib import Path
import yaml

logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s")


def read_config() -> dict:
    """Reads config from YAML file which is expected to be located in a file called 'config.yaml' in the same directory
    as this script.

    :return: dictionary containing set configuration
    """
    with Path("config.yaml").open("r") as file_pointer:
        try:
            return yaml.safe_load(file_pointer)
        except yaml.YAMLError as e:
            logging.error(e)
