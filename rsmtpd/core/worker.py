import copy
import socket

from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.core.logger_factory import LoggerFactory
from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.base_data_command import BaseDataCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.action import *
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_451 import SmtpResponse451
from select import select
from typing import Dict, List, ClassVar

from rsmtpd.response.smtp_500 import SmtpResponse500


class Worker(object):
    """
    The main worker class. All incoming connections will be handled in a worker
    """

    __server_name = None
    __config_loader = None
    __logger_factory = None
    __logger = None
    __default_config = {
        "command_handler": "__default__"
    }

    __default_handler = {
        "__OPEN__": [{
            "module": "rsmtpd.handlers.reject_all",
            "class": "RejectAll"
        }],
        "QUIT": [{
            "module": "rsmtpd.handlers.quit",
            "class": "Quit"
        }],
        "__DEFAULT__": [{
            "module": "rsmtpd.handlers.reject_all",
            "class": "RejectAll"
        }]
    }

    # Whether the last data chunk ended with CRLF
    __last_data_chunk_ends_with_crlf = False
    __first_data_chunk = True

    _handler_config = None
    _shared_state = None

    def __init__(self, server_name: str, config_loader: ConfigLoader, logger_factory: LoggerFactory):
        self.__server_name = server_name
        self.__config_loader = config_loader
        self.__logger_factory = logger_factory
        self.__logger = logger_factory.get_module_logger(self)
        self._handler_config = None
        self._shared_state = None

    def handle_client(self, connection: socket, remote_address):
        # Load the config and initialize the shared state
        self._handler_config = self._get_handler_config()

        # Initialize the shared state
        self._shared_state = SharedState(remote_address)
        self.__logger.info("%s Starting SMTP session with %s:%s", self._shared_state.transaction_id,
                           self._shared_state.remote_ip, self._shared_state.remote_port)

        # Initialize the main command loop with the __OPEN__ command
        command = "__OPEN__"
        argument = None
        buffer_is_empty = self._is_buffer_is_empty(connection)

        # This is the main command loop; it can be told to handle a particular command or, if None, wait for the client
        self.__logger.debug("Entering main command loop")
        while True:
            if command is None:
                # Read the next command from the client
                command, argument, buffer_is_empty = self._read_command(connection)
                self.__logger.debug("%s Received command \"%s\" with argument of \"%s\"",
                                    self._shared_state.transaction_id, command, argument)

            # Run the command
            response = None
            if command is None:
                response = SmtpResponse500()
            elif command == "__DATA__":
                response = self._handle_data(connection)
            else:
                response = self._handle_command(command, argument, buffer_is_empty)

            if response is None:
                self.__logger.warning("%s Command handlers for %s command did not provide a response; issuing "
                                      "451 response to client and closing connection",
                                      self._shared_state.transaction_id, command)
                response = SmtpResponse451()

            if response.get_action() == FORCE_CLOSE:
                self.__logger.info("%s Forcefully ending SMTP session with %s:%s as requested by command handler",
                                   self._shared_state.transaction_id, self._shared_state.remote_ip,
                                   self._shared_state.remote_port)
                return

            if self._shared_state.esmtp_capable:
                self.__logger.info("%s Sending extended response to client with SMTP code %s",
                                   self._shared_state.transaction_id, response.get_code())
                connection.send(response.get_extended_smtp_response().replace("<domain>", self.__server_name).encode())
            else:
                self.__logger.info("%s Sending response to client with SMTP code %s",
                                   self._shared_state.transaction_id,
                                   response.get_code())
                connection.send(response.get_smtp_response().replace("<domain>", self.__server_name).encode())

            # Clear the command for the next loop iteration
            command = None

            # TODO: Handle all actions
            if response.get_action() == CLOSE:
                self.__logger.info("%s Ending SMTP session with %s:%s as requested by command handler",
                                   self._shared_state.transaction_id, self._shared_state.remote_ip,
                                   self._shared_state.remote_port)
                return
            elif response.get_action() == FORCE_CLOSE:
                return
            elif response.get_action() == CONTINUE:
                # Get the data in the next iteration
                command = "__DATA__"

    def _is_buffer_is_empty(self, connection: socket) -> bool:
        r, w, e = select([connection], [], [], 0.01)
        if len(r) > 0:
            self.__logger.debug("Input buffer is not empty")
            return False

        return True

    def _read_command(self, connection: socket) -> (str, str):
        # Peek into the data to know the exact size
        # TODO: Set a maximum line length in the config
        peek = connection.recv(8192, socket.MSG_PEEK)

        # TODO: Look for LF only to be less strict and more flexible
        index = peek.find(b"\r\n")

        if index >= 0:
            command_length = index + 2  # Get CRLF too; we'll strip it out later
        else:
            command_length = len(peek)

        # Now that we have the line, read from the buffer the exact line length + 2 (for cr/lf)
        # TODO: Handle UTF-8?
        try:
            line = connection.recv(command_length).decode("US-ASCII")

            # Split the command on the first space
            split_line = line.split(" ", maxsplit=1)
            command = split_line[0].strip()
            if len(split_line) == 2:
                argument = split_line[1].strip()
            else:
                argument = ""
        except Exception as ex:
            command = None
            argument = None
            self.__logger.info("Unable to read incoming command")
            self.__logger.info(ex, exc_info=True)

        return command, argument, len(peek) == command_length

    def _read_data(self, connection: socket) -> (str, bool, bool):
        # Peek into the data to know the exact size
        peek = connection.recv(8192, socket.MSG_PEEK)
        data_length = len(peek)

        # TODO: If the client is only talking with LF, search appropriately
        terminator_length = 5
        data_end = False
        if self.__last_data_chunk_ends_with_crlf:
            if peek.find(b".\r\n") == 0:
                data_end = True
                data_length = 0
                terminator_length = 3
        else:
            index = peek.find(b"\r\n.\r\n")
            if index >= 0:
                data_end = True
                data_length = index

        # Read the data for real now
        if data_end:
            data_chunk = connection.recv(terminator_length)
            data_chunk = data_chunk[:-terminator_length]
        else:
            data_chunk = connection.recv(data_length)

            # If a line begins with a period, remove it (RFC 5321 4.5.2)
            if (self.__first_data_chunk or self.__last_data_chunk_ends_with_crlf) and data_chunk[0] == b"."[0]:
                data_chunk = data_chunk[1:]
            else:
                data_chunk = data_chunk.replace(b"\r\n.", b"\r\n")

            # See if it ends with CRLF
            self.__last_data_chunk_ends_with_crlf = data_chunk[-2:] == b"\r\n"

        return data_chunk, data_end, len(peek) == data_length + terminator_length

    def _handle_command(self, command: str, argument: str, buffer_is_empty: bool) -> BaseResponse:
        command_handlers = self._get_command_config(command)
        response = None

        self._shared_state.current_command = self._shared_state.CurrentCommand()
        self._shared_state.current_command.buffer_is_empty = buffer_is_empty

        for command_handler in command_handlers:
            handler = self._get_handler(command_handler, BaseCommand)
            if handler is not None:
                try:
                    tmp_response = handler.handle(command, argument, self._shared_state)
                except Exception as e:
                    tmp_response = None
                    self.__logger.error("Command handler %s threw exception while handling \"%s\" command with "
                                        "argument \"%s\"; error: %s", type(handler).__name__, command, argument, str(e))

                if tmp_response is not None:
                    response = copy.deepcopy(tmp_response)
                    self._shared_state.current_command.response = copy.deepcopy(response)

        return response

    def _handle_data(self, connection: socket) -> BaseResponse:
        command_handlers = self._get_command_config("__DATA__")
        response = None

        # Get all the command handlers
        data_handlers = []
        for command_handler in command_handlers:
            handler = self._get_handler(command_handler, BaseDataCommand)
            if handler is not None:
                data_handlers.append(handler)

        # Read data in chunks and pass it to each of the handlers
        self.__last_data_chunk_ends_with_crlf = False
        self.__first_data_chunk = True
        while True:
            data, end, buffer_is_empty = self._read_data(connection)

            self.__first_data_chunk = False
            self._shared_state.current_command.buffer_is_empty = buffer_is_empty

            if len(data):
                for data_handler in data_handlers:
                    try:
                        data_handler.handle_data(data, self._shared_state)
                    except Exception as e:
                        self.__logger.error("Data handler %s threw exception while handling incoming data; error: %s ",
                                            type(data_handler).__name__, str(e))

            if end:
                break

        for data_handler in data_handlers:
            try:
                tmp_response = data_handler.handle_data_end(self._shared_state)
            except Exception as e:
                tmp_response = None
                self.__logger.error("Data handler %s threw exception while handling end of data; error: %s ",
                                    type(data_handler).__name__, str(e))

            if tmp_response is not None:
                response = copy.deepcopy(tmp_response)
                self._shared_state.current_command.response = copy.deepcopy(response)

        return response

    def _get_handler_config(self) -> Dict:
        # Load the config for the worker; we do it every time so that daemon doesn't have to restart for changes to work
        # TODO: Cache instances and configs in this transaction for consistent behavior and better performance
        config = self.__config_loader.load(self, "", self.__default_config)

        config_name = config["command_handler"]
        handler_config = self.__default_handler
        if handler_config is None or len(handler_config) == 0 or handler_config == "__default__":
            self.__logger.warning("Warning: using default command handler")
        else:
            handler_config = self.__config_loader.load_by_name("command_handler", config_name, handler_config)

        return handler_config

    def _get_command_config(self, command: str) -> List[Dict]:
        """
        Loads the list of command handlers for the given SMTP command, falling back to the default command handler list
        if necessary.

        :param command: Command to get the config for

        :return: List of command handlers
        """
        command_config = None
        if command.upper() in self._handler_config:
            command_config = self._handler_config[command.upper()]
        elif "__DEFAULT__" in self._handler_config:
            self.__logger.debug("%s No command configuration for command \"%s\"; using default config",
                                self._shared_state.transaction_id, command)
            command_config = self._handler_config["__DEFAULT__"]
        return command_config

    def _get_handler(self, command_config: Dict, class_type: ClassVar):
        if command_config:
            try:
                module = __import__(command_config["module"])
                for sub in command_config["module"].split(".")[1:]:
                    module = getattr(module, sub)
                class_ref = getattr(module, command_config["class"])
                if issubclass(class_ref, class_type):
                    self.__logger.debug("Instantiating class %s in module %s", command_config["class"],
                                        command_config["module"])
                    # TODO: Implement suffixes
                    instance = class_ref(self.__logger_factory.get_module_logger(class_ref), self.__config_loader, "")
                    self.__logger.debug("Class %s in module %s successfully instantiated", command_config["class"],
                                        command_config["module"])
                    return instance
                else:
                    self.__logger.error("Class %s in module %s does not inherit from BaseCommand; handler ignored",
                                        command_config["class"], command_config["module"])
                    return None
            except Exception as e:
                self.__logger.error("Unable to load class: %s.%s does not exist (%s)", command_config["module"],
                                    command_config["class"], e)
                return None
