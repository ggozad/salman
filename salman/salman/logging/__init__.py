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
transcription_logger = logging.getLogger("transcription")
segmentation_logger = logging.getLogger("segmentation")
cleanup_logger = logging.getLogger("cleanup")
recorder_logger = logging.getLogger("recorder")
