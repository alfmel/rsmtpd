import os
from rsmtpd.handlers.base_data_command import BaseDataCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse


class PostDataResetDataHandler(BaseDataCommand):
    def handle_data(self, data: bytes, shared_state: SharedState):
        pass

    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        shared_state.mail_from = None
        shared_state.recipients = set()
        if shared_state.data_filename and not self._config.get("keep_data_file"):
            try:
                os.unlink(shared_state.data_filename)
            except Exception as e:
                self._logger.warning("Error attempting to delete data file; ignoring and clearing state", e)
        shared_state.data_filename = None

        return shared_state.current_command.response
