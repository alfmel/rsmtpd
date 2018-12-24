from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_500 import SmtpResponse500


class UnknownCommand(BaseCommand):
    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        return SmtpResponse500()
