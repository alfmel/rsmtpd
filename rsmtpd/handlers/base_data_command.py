from abc import ABCMeta, abstractmethod
from logging import Logger
from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from typing import Dict


class BaseDataCommand(metaclass=ABCMeta):
    """
    Base SMTP data command handler. All commands capable of handling the SMTP DATA command must extend this class.
    """

    __config_loader = None
    __config_suffix = ""
    _logger = None

    def __init__(self, logger: Logger, config_loader: ConfigLoader, config_suffix: str=""):
        self._logger = logger
        self.__config_loader = config_loader
        self.__config_suffix = config_suffix

    def _load_config(self, default_config: Dict) -> Dict:
        return self.__config_loader.load(self, suffix=self.__config_suffix, default=default_config)

    @abstractmethod
    def handle_data(self, data: bytes, shared_state: SharedState):
        raise NotImplementedError("Abstract method handle_data() must be implemented in child class")

    @abstractmethod
    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        raise NotImplementedError("Abstract method handle_data_end() must be implemented in child class")
