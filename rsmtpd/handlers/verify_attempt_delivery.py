from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_252 import SmtpResponse252


class VerifyAttemptDeliveryHandler(BaseCommand):
    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        # TODO: Verify email address is in list of accepted domains
        return SmtpResponse252()
