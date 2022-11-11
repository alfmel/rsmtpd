from abc import ABCMeta, abstractmethod
from logging import Logger
from typing import Dict
from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse


class Command(metaclass=ABCMeta):
    def __init__(self, logger: Logger, config_loader: ConfigLoader, config_suffix: str = "", default_config: Dict = {}):
        self._logger = logger
        self._config = config_loader.load(self, suffix=config_suffix, default=default_config)


class BaseCommand(Command):
    """
    Base SMTP command handler. All handlers must extend this class and implement the handle() method.
    """

    @abstractmethod
    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        raise NotImplementedError("Abstract method handle() must be implemented in child class")
