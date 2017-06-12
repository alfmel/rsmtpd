import socket

from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.core.logger_factory import LoggerFactory
from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.action import CLOSE, FORCE_CLOSE
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_451 import SmtpResponse451
from select import select
from typing import Dict, List


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

        # Run the command
        response = self._handle_command("__open__", "", self._is_buffer_empty(connection))

        if response is None:
            self.__logger.warning("%s Command handlers for \"__open__\" command did not provide a response; "
                                  "issuing permanent 451 response to client", self._shared_state.transaction_id)
            response = SmtpResponse451(permanent=True)

        if response.get_action() == FORCE_CLOSE:
            self.__logger.info("%s Forcefully ending SMTP session with %s:%s as requested by command handler",
                               self._shared_state.transaction_id, self._shared_state.remote_ip,
                               self._shared_state.remote_port)
            return

        self.__logger.info("%s Sending opening message to client with SMTP code %s", self._shared_state.transaction_id,
                           response.get_code())
        connection.send(response.get_smtp_response().replace("<domain>", self.__server_name).encode())

        if response.get_action() == CLOSE:
            self.__logger.info("%s Ending SMTP session with %s:%s as requested by command handler",
                               self._shared_state.transaction_id, self._shared_state.remote_ip,
                               self._shared_state.remote_port)
            return

        # Read commands and handle them until it's time to close the connection
        while True:
            self.__logger.debug("Entering main command loop")

            command, argument = self._read_command(connection)
            self.__logger.debug("%s Received command \"%s\" with argument of \"%s\"", self._shared_state.transaction_id,
                                command, argument)
            response = self._handle_command(command, argument, self._is_buffer_empty(connection))

            # TODO: Handle all actions
            if response.get_action() == FORCE_CLOSE:
                self.__logger.info("%s Forcefully ending SMTP session with %s:%s as requested by command handler",
                                   self._shared_state.transaction_id, self._shared_state.remote_ip,
                                   self._shared_state.remote_port)
                return

            self.__logger.info("%s Sending response to client with SMTP code %s", self._shared_state.transaction_id,
                               response.get_code())
            connection.send(response.get_smtp_response().replace("<domain>", self.__server_name).encode())

            if response.get_action() == CLOSE:
                self.__logger.info("%s Ending SMTP session with %s:%s as requested by command handler",
                                   self._shared_state.transaction_id, self._shared_state.remote_ip,
                                   self._shared_state.remote_port)
                return

    def _is_buffer_empty(self, connection: socket) -> bool:
        r, w, e = select([connection], [], [], 0.01)
        if len(r) > 0:
            self.__logger.debug("Input buffer is not empty")
            return True

        return False

    def _read_command(self, connection: socket) -> (str, str):
        # Peek into the data to know the exact size
        # TODO: Set a maximum line length in the config
        peek = connection.recv(8192, socket.MSG_PEEK)

        # TODO: Split on LF only to be less strict
        lines = peek.decode("US-ASCII").split("\r\n")

        # Now that we have the line, read from the buffer the exact line length + 2 (for cr/lf)
        # TODO: Handle UTF-8?
        line = connection.recv(len(lines[0]) + 2).decode("US-ASCII")

        # Split the command on the first space
        split_line = line.split(" ", maxsplit=1)
        command = split_line[0].strip()
        if len(split_line) == 2:
            argument = split_line[1].strip()
        else:
            argument = ""

        return command, argument

    def _handle_command(self, command: str, argument: str, buffer_empty: bool) -> BaseResponse:
        command_handlers = self._get_command_config(command)
        response = None
        for command_handler in command_handlers:
            handler = self._get_handler(command_handler)
            if handler is not None:
                response = handler.handle(command, argument, buffer_empty, self._shared_state)

                # TODO: Combine responses

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

    def _get_handler(self, command_config: Dict):
        if command_config:
            try:
                module = __import__(command_config["module"])
                for sub in command_config["module"].split(".")[1:]:
                    module = getattr(module, sub)
                class_ref = getattr(module, command_config["class"])
                if issubclass(class_ref, BaseCommand):
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
