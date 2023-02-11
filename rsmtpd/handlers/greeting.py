from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_220 import SmtpResponse220


class GreetingHandler(BaseCommand):
    """
    The built-in command that greets the client when the server is ready to receive email
    """

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if "message" in self._config:
            return SmtpResponse220(alt_message=self._config["message"])

        return SmtpResponse220()
