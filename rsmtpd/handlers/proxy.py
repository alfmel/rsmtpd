from socket import socket

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

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        sock = None
        if hasattr(shared_state, "proxy"):
            sock = shared_state.proxy["socket"]
        else:
            shared_state.proxy = {
                "socket": None,
                "smtp_socket": None,
                "helo_response": None
            }
        cmd = command.upper()

        try:
            if cmd == "__OPEN__":
                sock, response = self._connect_to_remote_server(shared_state)
            elif cmd == "STARTTLS":
                response = SmtpResponse220StartTLS()
            elif cmd in ["HELO", "EHLO"] and shared_state.proxy["helo_response"]:
                response = shared_state.proxy["helo_response"]
            else:
                smtp_socket = shared_state.proxy["smtp_socket"]
                if command.upper() == "EHLO":
                    shared_state.esmtp_capable = True
                smtp_socket.write(self._create_command(command, argument))

                # TODO: Detect and enable UTF-8 support
                data = self._read_multiline_response(smtp_socket).decode("US-ASCII")
                response = self._parse_and_generate_response(data, shared_state, command)

            if response.get_action() in [CLOSE, FORCE_CLOSE]:
                self._disconnect_from_remote_server(sock)
            return response
        except RemoteConnectionClosedException:
            self._disconnect_from_remote_server(sock)
            return ProxyResponse(500, "Connection lost", action=CLOSE)
        except Exception:
            self._disconnect_from_remote_server(sock)
            return ProxyResponse(500, "Unknown error", action=CLOSE)

    def _connect_to_remote_server(self, shared_state: SharedState) -> (socket, BaseResponse):
        config = self._load_config(self._default_config)
        sock = socket()
        self._logger.info("Connecting to {} port {}".format(config["host"], config["port"]))
        sock.connect((config["host"], config["port"]))
        shared_state.proxy["socket"] = sock
        smtp_socket = SMTPSocket(sock)
        shared_state.proxy["smtp_socket"] = smtp_socket
        # TODO: Handle UTF-8
        data = smtp_socket.read_line().decode("US-ASCII")
        return sock, self._parse_and_generate_response(data, shared_state)

    def _disconnect_from_remote_server(self, sock: socket) -> None:
        if sock:
            try:
                self._logger.info("Disconnecting from remote host")
                sock.close()
            except Exception:
                pass

    def handle_data(self, data: bytes, shared_state: SharedState) -> BaseResponse:
        sock = shared_state.proxy["socket"]
        smtp_socket = shared_state.proxy["smtp_socket"]
        try:
            smtp_socket.write(data)
        except RemoteConnectionClosedException:
            self._disconnect_from_remote_server(sock)
            return ProxyResponse(500, "Connection lost", action=CLOSE)
        except Exception:
            self._disconnect_from_remote_server(sock)
            return ProxyResponse(500, "Unknown error", action=CLOSE)

    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        sock = shared_state.proxy["socket"]
        smtp_socket = shared_state.proxy["smtp_socket"]
        try:
            smtp_socket.write(b".\r\n")
            data = self._read_multiline_response(smtp_socket).decode("US-ASCII")
            return self._parse_and_generate_response(data, shared_state)
        except RemoteConnectionClosedException:
            self._disconnect_from_remote_server(sock)
            return ProxyResponse(500, "Connection lost", action=CLOSE)
        except Exception:
            self._disconnect_from_remote_server(sock)
            return ProxyResponse(500, "Unknown error", action=CLOSE)

    def _read_multiline_response(self, smtp_socket: SMTPSocket) -> bytes:
        line = smtp_socket.read_line()
        data = line
        while line[3] != 32:  # space
            line = smtp_socket.read_line()
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
                shared_state.proxy["helo_response"] = response
                if shared_state.tls_available and not shared_state.tls_enabled:
                    multi_line_message_with_starttls = multi_line_message.copy()
                    multi_line_message_with_starttls.append("STARTTLS")
                    response = ProxyResponse(smtp_code, message, multi_line_message_with_starttls)
            return response
