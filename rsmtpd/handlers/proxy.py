from socket import socket

from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.base_data_command import BaseDataCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.proxy_response import ProxyResponse
from rsmtpd.response.smtp_221 import SmtpResponse221
from rsmtpd.response.smtp_354 import SmtpResponse354


class Proxy(BaseCommand, BaseDataCommand):
    _default_config = {
        "host": None,
        "port": None
    }

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if command.upper() == "__OPEN__":
            config = self._load_config(self._default_config)
            connection = socket()
            connection.connect((config["host"], config["port"]))
            shared_state.proxy = {
                "connection": connection
            }
            data = connection.recv(8192).decode("US-ASCII")
            return self._parse_and_generate_response(data)
        else:
            connection = shared_state.proxy["connection"]
            if command.upper() == "EHLO":
                shared_state.esmtp_capable = True
            connection.send(self._create_command(command, argument))
            # TODO: Detect and enable UTF-8 support
            data = connection.recv(8192).decode("US-ASCII")
            return self._parse_and_generate_response(data, command.upper() == "EHLO")

    def handle_data(self, data: bytes, shared_state: SharedState):
        connection = shared_state.proxy["connection"]
        connection.send(data)

    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        connection = shared_state.proxy["connection"]
        connection.send(".\r\n".encode())
        data = connection.recv(8192).decode("US-ASCII").strip()
        return self._parse_and_generate_response(data)

    def _create_command(self, command: str, argument: str) -> bytes:
        if argument:
            return (command + " " + argument + "\r\n").encode()
        else:
            return (command + "\r\n").encode()

    def _parse_and_generate_response(self, data: str, is_ehlo: bool = False) -> BaseResponse:
        # Handle both CRLF and LF
        lines = data.split("\r\n")
        if len(lines) == 1:
            lines = data.split("\n")

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
                    if is_ehlo:
                        if message != "STARTTLS" and not message.startswith("AUTH"):
                            multi_line_message.append(message)
                    else:
                        multi_line_message.append(message)

        if smtp_code == "354":
            return SmtpResponse354(message)
        elif smtp_code == "221":
            return SmtpResponse221(message, multi_line_message)
        else:
            return ProxyResponse(smtp_code, message, multi_line_message)
