from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_354 import SmtpResponse354
from rsmtpd.response.smtp_501 import SmtpResponse501
from rsmtpd.response.smtp_503 import SmtpResponse503


class DataHandler(BaseCommand):
    """
    The built-in command handler for the DATA command. It verifies we are ready to receive email and beings the DATA
    transmission part of the SMTP session.
    """

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if argument:
            return SmtpResponse501()

        if shared_state.client_name is None:
            return SmtpResponse503("You must say HELO/EHLO before using this command")

        if not shared_state.mail_from:
            return SmtpResponse503("You must first use the MAIL command before attempting to send DATA")

        if not len(shared_state.recipients):
            return SmtpResponse503("You must provide one or more valid recipients before attempting to send DATA")

        return SmtpResponse354()
