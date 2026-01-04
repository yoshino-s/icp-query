import logging
import sys

import coloredlogs
import verboselogs
from pythonjsonlogger.json import JsonFormatter

from .config import LoggingConfig


def init_logger(config: LoggingConfig, env: str):
    verboselogs.install()
    if env == "production":
        handler = logging.StreamHandler(sys.stderr)
        formatter = JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            json_ensure_ascii=False,
        )
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
    else:
        coloredlogs.install(
            level=logging.DEBUG,
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            stream=sys.stderr,
        )
    logging.root.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    logging.getLogger("httpcore").setLevel(logging.WARNING)
