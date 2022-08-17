from rsmtpd.core.validation import parse_email_address_input, EmailAddressVerificationResult
from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.response.smtp_501 import SmtpResponse501
from rsmtpd.response.smtp_503 import SmtpResponse503
from rsmtpd.response.smtp_504 import SmtpResponse504


class RecipientHandler(BaseCommand):
    """
    The built-in command handler for the RCPT command (only handles RCPT TO)
    """

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if shared_state.client_name is None:
            return SmtpResponse503("You must say HELO/EHLO before using this command")

        if not argument.upper().startswith("TO:"):
            return SmtpResponse504("Only RCPT TO> is implemented on this server")

        parsed_email = parse_email_address_input(argument.split(":", 1)[1])

        if not parsed_email.is_valid:
            return SmtpResponse501("Email address does not appear to be valid")

        # TODO: Verify email address is accepted by this server
        verified_email = EmailAddressVerificationResult(parsed_email, True)

        shared_state.recipients.add(verified_email)

        return SmtpResponse250()
