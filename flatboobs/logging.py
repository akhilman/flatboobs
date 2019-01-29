# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name

import logging
import logging.config
from typing import Any, Dict, Optional


CRITICAL = logging.CRITICAL
DEBUG = logging.DEBUG
ERROR = logging.ERROR
FATAL = logging.FATAL
INFO = logging.INFO
NOTSET = logging.NOTSET
WARNING = logging.WARNING


class Logger:

    def __init__(self: 'Logger', name: str = 'slivoglot'):

        self.__name: str = name
        self.__logger: Optional[logging.Logger] = None

    def __getattr__(self: 'Logger', key: str) -> Any:

        if not self.__logger:
            self.__logger = logging.getLogger(self.__name)

        return getattr(self.__logger, key)


_instances: Dict[str, Logger] = dict()


def getLogger(name: str = 'flatboobs') -> Logger:
    if name not in _instances:
        _instances[name] = Logger(name)
    return _instances[name]


def setup_logging(
        debug: bool = False,
) -> Logger:

    level = DEBUG if debug else INFO
    logging.basicConfig(level=level)

    logger = getLogger()
    logger.setLevel(level)

    return logger


__all__ = [
    'CRITICAL', 'DEBUG', 'ERROR', 'FATAL', 'INFO', 'NOTSET', 'WARNING',
    'getLogger', 'setup_logging',
]
