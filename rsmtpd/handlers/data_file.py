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
            except Exception:
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
        ip_and_port = f"{shared_state.client.ip}:{shared_state.client.port}"
        client_host_name = shared_state.client_name.reverse_dns_name
        tls_enabled = "enabled" if shared_state.client.tls_enabled else "disabled"
        helo = "EHLO" if shared_state.esmtp_capable else "HELO"
        datetime_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")

        headers = f"Return-Path: <{shared_state.mail_from.email_address}>\r\n" \
                  f"Received: from [{ip_and_port}] {client_host_name} TLS {tls_enabled}\r\n" \
                  f"          with {helo} {shared_state.client.advertised_name}\r\n" \
                  f"          on {datetime_str} by RSMTPD {shared_state.server_version}\r\n"

        self.__mail_file.write(bytes(headers, "UTF8"))
