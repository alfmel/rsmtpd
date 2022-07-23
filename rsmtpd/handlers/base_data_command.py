from abc import abstractmethod

from rsmtpd.handlers.base_command import Command
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse


class BaseDataCommand(Command):
    """
    Base SMTP data command handler. All commands capable of handling the SMTP DATA command must extend this class.
    """

    @abstractmethod
    def handle_data(self, data: bytes, shared_state: SharedState):
        raise NotImplementedError("Abstract method handle_data() must be implemented in child class")

    @abstractmethod
    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        raise NotImplementedError("Abstract method handle_data_end() must be implemented in child class")
