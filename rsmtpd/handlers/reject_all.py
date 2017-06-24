from rsmtpd.handlers.base_command import BaseCommand, ConfigLoader, Logger, SharedState
from rsmtpd.response.smtp_521 import SmtpResponse521, BaseResponse


class RejectAll(BaseCommand):
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
        return SmtpResponse521(close_on_connect=config["close_connection"])
