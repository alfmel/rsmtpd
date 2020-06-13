from logging import Logger
from socket import socket

from rsmtpd import ConfigLoader
from rsmtpd.core.smtp_socket import SMTPSocket
from rsmtpd.exceptions import RemoteConnectionClosedException
from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.base_data_command import BaseDataCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.action import CLOSE, FORCE_CLOSE
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.proxy_response import ProxyResponse
from rsmtpd.response.smtp_220_start_tls import SmtpResponse220StartTLS
from rsmtpd.response.smtp_221 import SmtpResponse221
from rsmtpd.response.smtp_354 import SmtpResponse354


class Proxy(BaseCommand, BaseDataCommand):
    _default_config = {
        "host": None,
        "port": None
    }

    def __init__(self, logger: Logger, config_loader: ConfigLoader, config_suffix: str = ""):
        super().__init__(logger, config_loader, config_suffix, Proxy._default_config)
        self._socket: socket
        self._smtp_socket: SMTPSocket
        self._helo_response: str = ""

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        cmd = command.upper()
        try:
            if cmd == "__OPEN__":
                response = self._connect_to_remote_server(shared_state)
            elif cmd == "STARTTLS":
                response = SmtpResponse220StartTLS()
            elif cmd in ["HELO", "EHLO"] and self._helo_response:
                response = self._helo_response
            else:
                if cmd == "EHLO":
                    shared_state.esmtp_capable = True
                self._smtp_socket.write(self._create_command(command, argument))

                # TODO: Detect and enable UTF-8 support
                data = self._read_multiline_response().decode("US-ASCII")
                response = self._parse_and_generate_response(data, shared_state, command)

            if response.get_action() in [CLOSE, FORCE_CLOSE]:
                self._disconnect_from_remote_server()
            return response
        except RemoteConnectionClosedException:
            self._disconnect_from_remote_server()
            return ProxyResponse(500, "Connection lost", action=CLOSE)
        except Exception as e:
            self._logger.error(e)
            self._disconnect_from_remote_server()
            return ProxyResponse(500, "Unknown error", action=CLOSE)

    def _connect_to_remote_server(self, shared_state: SharedState) -> BaseResponse:
        self._socket = socket()
        self._logger.info("Connecting to {} port {}".format(self._config["host"], self._config["port"]))
        self._socket.connect((self._config["host"], self._config["port"]))
        self._smtp_socket = SMTPSocket(self._socket)
        # TODO: Handle UTF-8
        data = self._smtp_socket.read_line().decode("US-ASCII")
        return self._parse_and_generate_response(data, shared_state)

    def _disconnect_from_remote_server(self) -> None:
        if self._socket:
            try:
                self._logger.info("Disconnecting from remote host")
                self._socket.close()
                self._socket = None
            except Exception:
                pass

    def handle_data(self, data: bytes, shared_state: SharedState) -> BaseResponse:
        try:
            self._smtp_socket.write(data)
        except RemoteConnectionClosedException:
            self._disconnect_from_remote_server()
            return ProxyResponse(500, "Connection lost", action=CLOSE)
        except Exception as e:
            self._logger.error(e)
            self._disconnect_from_remote_server()
            return ProxyResponse(500, "Unknown error", action=CLOSE)

    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        try:
            self._smtp_socket.write(b".\r\n")
            data = self._read_multiline_response().decode("US-ASCII")
            return self._parse_and_generate_response(data, shared_state)
        except RemoteConnectionClosedException:
            self._disconnect_from_remote_server()
            return ProxyResponse(500, "Connection lost", action=CLOSE)
        except Exception as e:
            self._logger.error(e)
            self._disconnect_from_remote_server()
            return ProxyResponse(500, "Unknown error", action=CLOSE)

    def _read_multiline_response(self) -> bytes:
        line = self._smtp_socket.read_line()
        data = line
        while line[3] != 32:  # space
            line = self._smtp_socket.read_line()
            if len(line) == 0:
                break
            data += line
        return data

    def _create_command(self, command: str, argument: str) -> bytes:
        if argument:
            return (command + " " + argument + "\r\n").encode()
        else:
            return (command + "\r\n").encode()

    def _parse_and_generate_response(self, data: str, shared_state: SharedState, command: str = "") -> BaseResponse:
        cmd = command.upper()

        lines = []
        for line in data.strip().split("\n"):
            lines.append(line.strip())

        # See if this is a multi-line response
        smtp_code = 0
        if len(lines) == 2:
            smtp_code = lines[0][0:3]
            message = lines[0][4:]
            multi_line_message = [message]
        else:
            message = ""
            multi_line_message = []
            for line in lines:
                if line:
                    if line[3] == " ":
                        smtp_code = line[0:3]
                    message = line[4:]
                    if cmd == "EHLO":
                        if message != "STARTTLS" and not message.startswith("AUTH"):
                            multi_line_message.append(message)
                    else:
                        multi_line_message.append(message)

        if smtp_code == "354":
            return SmtpResponse354(message)
        elif smtp_code == "221":
            return SmtpResponse221(message, multi_line_message)
        else:
            response = ProxyResponse(smtp_code, message, multi_line_message)
            if cmd == "HELO" or cmd == "EHLO":
                # Cache HELO/EHLO response for TLs reset without STARTTLS
                self._helo_response = response
                if shared_state.tls_available and not shared_state.tls_enabled:
                    multi_line_message_with_starttls = multi_line_message.copy()
                    multi_line_message_with_starttls.append("STARTTLS")
                    response = ProxyResponse(smtp_code, message, multi_line_message_with_starttls)
            return response
