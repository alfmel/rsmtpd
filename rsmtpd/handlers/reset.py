import os
from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.response.smtp_501 import SmtpResponse501


class ResetHandler(BaseCommand):
    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if argument:
            return SmtpResponse501()

        shared_state.mail_from = None
        shared_state.recipients = set()
        if shared_state.data_filename:
            try:
                os.unlink(shared_state.data_filename)
            except Exception as e:
                self._logger.warning("Error attempting to delete data file; ignoring and clearing state", e)
            finally:
                shared_state.data_filename = None

        return SmtpResponse250()
