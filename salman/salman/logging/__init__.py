import logging
import logging.config
from pathlib import Path

import yaml


def setup_logging():
    """Setup logging configuration"""
    path = Path(__file__).parent / "logging.yaml"
    with open(path, "rt") as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)


setup_logging()
salman = logging.getLogger("salman")
