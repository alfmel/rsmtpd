import os
from datetime import datetime
from logging import Logger
from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.handlers.base_data_command import BaseDataCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.response.smtp_451 import SmtpResponse451
from rsmtpd.response.smtp_552 import SmtpResponse552
from typing import Dict


class DataToFileDataHandler(BaseDataCommand):
    def __init__(self, logger: Logger, config_loader: ConfigLoader, config_suffix: str = "", default_config: Dict = {}):
        super().__init__(logger, config_loader, config_suffix, default_config)
        self.__mail_spool_dir = self._config.get("mail_spool_dir", "/var/tmp")
        self.__mail_file = None
        self.__size = 0
        self.__error = False

    def handle_data(self, data: bytes, shared_state: SharedState):
        if not self.__error:
            try:
                if not self.__mail_file:
                    filename = "{}/rsmtpd-{}.txt".format(self.__mail_spool_dir, shared_state.transaction_id)
                    self.__mail_file = open(filename, "bw")
                    shared_state.data_filename = filename
                    self._write_envelope(shared_state)

                self.__size += len(data)
                if self.__size <= shared_state.max_message_size:
                    self.__mail_file.write(data)
            except Exception as e:
                self._logger.error("Error handling data", e)
                self.__error = True

    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        if self.__mail_file:
            try:
                self.__mail_file.close()
            except:
                pass

        if self.__error:
            return SmtpResponse451("Unable to deliver message at this time. Please try again later.")

        if self.__size > shared_state.max_message_size:
            os.unlink(shared_state.data_filename)
            shared_state.data_filename = None
            return SmtpResponse552("Data rejected: size of {} exceeds maximum size of {}".format(
                self.__size, shared_state.max_message_size))

        return SmtpResponse250()

    def _write_envelope(self, shared_state):
        headers = "Return-Path: <{}>\r\n".format(shared_state.mail_from.email_address) + \
                  "Received: from [{}:{}] {} TLS=\r\n".format(shared_state.client.ip,
                                                              shared_state.client.port,
                                                              "",  # TODO: Add reverse-lookup
                                                              shared_state.client.tls_enabled) + \
                  "          with helo {}\r\n".format(shared_state.client.advertised_name) + \
                  "          on {} by RSMTPD\r\n".format(datetime.now().strftime("%Y-%m-%dT%H%:M%:%S%z"))
        self.__mail_file.write(bytes(headers, "UTF8"))
