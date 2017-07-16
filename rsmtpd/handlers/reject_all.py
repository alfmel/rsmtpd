from rsmtpd.handlers.base_command import BaseCommand, SharedState
from rsmtpd.handlers.base_data_command import BaseDataCommand
from rsmtpd.response.smtp_351 import SmtpResponse351, BaseResponse
from rsmtpd.response.smtp_521 import SmtpResponse521


class RejectAll(BaseCommand, BaseDataCommand):
    """
    A command handler that always returns SMTP code 521 in accordance to RFC 7504.

    Optional configuration allows you to specify whether the connection should be immediately closed or if other
    commands are accepted.
    """

    _config = None
    _default_config = {
        "close_connection": True
    }

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        config = self._load_config(self._default_config)
        if config["close_connection"]:
            return SmtpResponse521(close_on_connect=True)
        elif command.upper() == "DATA":
            return SmtpResponse351()
        else:
            return SmtpResponse521(close_on_connect=False)

    def handle_data(self, data: bytes, shared_state: SharedState):
        pass

    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        return SmtpResponse521(close_on_connect=False)
