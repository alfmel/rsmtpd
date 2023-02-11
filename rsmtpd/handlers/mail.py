from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.response.smtp_501 import SmtpResponse501
from rsmtpd.response.smtp_503 import SmtpResponse503
from rsmtpd.response.smtp_504 import SmtpResponse504
from rsmtpd.validators.email_address.parser import parse_email_address_input


class MailHandler(BaseCommand):
    """
    The built-in command handler for the MAIL command (only handles MAIL FROM)
    """

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if shared_state.client_name is None:
            return SmtpResponse503("You must say HELO/EHLO before using this command")

        if not argument.upper().startswith("FROM:"):
            return SmtpResponse504("Only MAIL FROM: is implemented on this server")

        shared_state.mail_from = parse_email_address_input(argument.split(":", 1)[1], True)

        if not shared_state.mail_from.is_valid:
            return SmtpResponse501("Email address does not appear to be valid")

        if shared_state.mail_from.email_address == "":
            return SmtpResponse250("Accepting bounced message")

        return SmtpResponse250()
