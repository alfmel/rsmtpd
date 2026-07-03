import spf
from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_450 import SmtpResponse450
from rsmtpd.response.smtp_550 import SmtpResponse550


class SpfValidator(BaseCommand):
    """
    Runs an SPF check on the client. If it fails, it will reject the MAIL FROM command
    """

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if not shared_state.current_command.response or shared_state.current_command.response.get_code() != 250:
            self._logger.warning("Skipping SPF check: previous response not 250")
            return shared_state.current_command.response

        if not shared_state.mail_from or shared_state.mail_from.email_address == "":
            self._logger.warning("Skipping SPF check: empty MAIL FROM address")
            return shared_state.current_command.response

        if not shared_state.mail_from.is_valid:
            self._logger.warning("Skipping SPF check: invalid SPF")
            return shared_state.current_command.response

        (result, message) = spf.check2(shared_state.client.ip,
                                       shared_state.mail_from.email_address,
                                       shared_state.client_name)

        if result in ["permerror", "fail", "softfail"]:
            shared_state.mail_from.is_valid = False
            self._logger.warning(f"Client failed SPF check: {result} {message}")
            return SmtpResponse550("Sender Policy Framework says you are not authorized")
        elif result in ["temperror"]:
            self._logger.warning(f"Error performing SPF check: {result} {message}")
            shared_state.mail_from.is_valid = False
            return SmtpResponse450("Temporary error while applying Sender Policy Framework; please try again later")

        self._logger.debug(f"SPF check passed: {result} {message}")
        return shared_state.current_command.response
