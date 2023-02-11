from logging import Logger
from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.core.logger_factory import LoggerFactory
from socket import socket
from typing import Dict, Union
from unittest.mock import Mock


class StubLoggerFactory(LoggerFactory):
    def get_module_logger(self, module: object):
        return MockLogger("mock_logger")


class MockLogger(Logger):
    critical = Mock(return_value=None)
    error = Mock(return_value=None)
    warning = Mock(return_value=None)
    info = Mock(return_value=None)
    debug = Mock(return_value=None)


class MockConfigLoader(ConfigLoader):
    def __init__(self, logger_factory: LoggerFactory, config: dict = None):
        super().__init__(logger_factory)
        self._config = config

    def load(self, class_ref: object, suffix: str = "", default: Dict = None):
        if self._config is None:
            return default
        else:
            return self._config

    def load_by_name(self, name: str, suffix: str = "", default: Dict = None):
        if self._config is None:
            return default
        else:
            return self._config

    def set_mock_config(self, config: Union[dict, None]):
        self._config = config


def get_mock_socket() -> Mock(socket):
    return Mock(socket)
