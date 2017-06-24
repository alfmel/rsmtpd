from rsmtpd.handlers.base_command import BaseCommand, ConfigLoader, Logger, SharedState
from rsmtpd.response.smtp_221 import SmtpResponse221, BaseResponse
from rsmtpd.response.smtp_501 import SmtpResponse501


class Quit(BaseCommand):
    """
    A command handler for the SMTP QUIT command. This command is implemented according to RFC 5321, including the 501
    response recommended in section 4.3.2.
    """

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        # Note: this command does not have any configuration
        if argument:
            return SmtpResponse501()
        else:
            return SmtpResponse221()
