import os
import subprocess

from rsmtpd.handlers.base_data_command import BaseDataCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.response.smtp_450 import SmtpResponse450


class DovecotDelivery(BaseDataCommand):
    def handle_data(self, data: bytes, shared_state: SharedState):
        pass

    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        if shared_state.current_command.response.get_code() != 250:
            self._logger.warning(f"Email {shared_state.transaction_id} will not be delivered as it lacks 250 response "
                                 f"(actual code: {shared_state.current_command.response.get_code()} "
                                 f"{shared_state.current_command.response.get_message()})")
            return shared_state.current_command.response

        if not shared_state.data_filename:
            self._logger.error(f"Cannot deliver email for {shared_state.transaction_id}: data filename missing")
            return SmtpResponse450()

        if not os.path.exists(shared_state.data_filename):
            self._logger.error(f"Cannot deliver email for {shared_state.transaction_id}: data file does not exist")
            return SmtpResponse450()

        try:
            for recipient in shared_state.recipients:
                with open(shared_state.data_filename, 'rb') as data_stream:
                    self._logger.info(f"Attempting to deliver {shared_state.transaction_id} to {recipient.deliver_to}")
                    result = subprocess.run([self._config.get("dovecot_lda_path", "/usr/lib/dovecot/dovecot-lda"),
                                             "-d", recipient.deliver_to], stdin=data_stream)
                    if result.returncode:
                        self._logger.error(f"Could not deliver email for {shared_state.transaction_id}: "
                                           f"dovecot-lda exited with return code {result.returncode}")
                        return SmtpResponse450()

                    self._logger.warning(f"Successfully delivered email from {shared_state.mail_from.email_address} "
                                         f"to {recipient.deliver_to}")

        except Exception as e:
            self._logger.error(f"Could not deliver email for {shared_state.transaction_id}", e)
            return SmtpResponse450()

        return SmtpResponse250()
