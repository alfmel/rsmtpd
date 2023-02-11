from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_220_start_tls import SmtpResponse220StartTLS
from rsmtpd.response.smtp_500 import SmtpResponse500
from rsmtpd.response.smtp_503 import SmtpResponse503


class StartTLS(BaseCommand):
    """
    A handler for starting TLS socket encryption
    """
    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if shared_state.client.tls_available:
            if shared_state.client.tls_enabled:
                return SmtpResponse503("TLS already started")
            return SmtpResponse220StartTLS()
        else:
            return SmtpResponse500()
