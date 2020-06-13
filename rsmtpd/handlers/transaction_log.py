"""
A set of command handlers that log commands and responses. There are three different loggers:

1. TransactionLog - Logs the given command and response in the shared_state. The logging of the command and response
   occurs at the same time when the command handler is invoked. That means there is only one timestamp associated with
   the entry. This command handler should come at the end of the command handler chain.

2. CommandLog - Logs the commands only. If placed at the beginning of the command chain, it will accurate log timestamps
   when a command is received. Responses are not logged.

3. ResponseLog - Logs the responses only. If placed at the end of the command chain, it will accurate log responses as
   they are about to be handled by the worker. It can also be inserted between commands in the command chain to log
   their responses.
"""

import os
import time
from datetime import datetime
from logging import Logger

from rsmtpd import ConfigLoader
from rsmtpd.handlers.base_command import BaseCommand, SharedState
from rsmtpd.handlers.base_data_command import BaseDataCommand


class TransactionLog(BaseCommand, BaseDataCommand):
    """
    A command handler that logs all commands and responses to a file. Each new SMTP transaction gets its own file.
    """
    _default_config = {
        "log_path": None
    }

    def __init__(self, logger: Logger, config_loader: ConfigLoader, config_suffix: str = ""):
        super().__init__(logger, config_loader, config_suffix, TransactionLog._default_config)
        self._initialized = False
        self._f = None

    def handle(self, command: str, argument: str, shared_state: SharedState) -> None:
        if not self._initialized:
            self._create_new_transaction_log(shared_state)
            self._initialized = True

        if self._f is not None:
            # Get a timestamp
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")

            # Figure out the state of the buffer
            buffer = "empty"
            if not shared_state.current_command.buffer_is_empty:
                buffer = "full"

            # Get the response
            response = None
            if shared_state.current_command.response:
                response = shared_state.current_command.response.get_extended_smtp_response()

            # Call the writer
            self._write(timestamp, buffer, command, argument, response)
            self._f.flush()

    def handle_data(self, data: bytes, shared_state: SharedState):
        if not self._initialized:
            self._create_new_transaction_log(shared_state)
            self._initialized = True

        if self._f is not None:
            self._f.write(data.decode("US-ASCII"))

    def handle_data_end(self, shared_state: SharedState):
        if self._f is not None:
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
            self._f.write("\r\n< {} End of DATA\r\n".format(timestamp))

            # Put the response together
            response_output = "< (No response)"
            if shared_state.current_command.response:
                response_output = "< {}".format(shared_state.current_command.response.get_smtp_response())
            self._f.write(response_output)

    def _write(self, timestamp: str, buffer_state: str, command: str, argument: str, response: str):
        # Put the command together
        command_output = "> {} [buffer: {}] {} {}\r\n".format(timestamp, buffer_state, command, argument)
        if not argument:
            command_output = "> {} [buffer: {}] {}\r\n".format(timestamp, buffer_state, command)

        # Write the command out to the file
        self._f.write(command_output)

        # Put the response together
        response_output = "< (No response)"
        if response:
            response_output = "< {}".format(response)

        self._f.write(response_output)

    def _create_new_transaction_log(self, shared_state: SharedState):
        if self._config["log_path"]:
            try:
                if not os.path.isdir(self._config["log_path"]):
                    os.mkdir(self._config["log_path"])
                filename = "{}-{}-{}.log".format(time.strftime("%Y%m%dT%H%M%S"), shared_state.remote_ip,
                                                 shared_state.transaction_id)
                full_path = os.path.join(self._config["log_path"], filename)

                self._f = open(full_path, "w")
                self._logger.info("Transaction log file created: %s", full_path)
            except Exception as e:
                self._logger.error("Could not open transaction log in %s (%s): "
                                   "logging disabled for this transaction", self._config["log_path"], e)
        else:
            self._logger.warning("Transaction logger has not been configured; transaction logs have been disabled")


class CommandLog(TransactionLog):
    def _write(self, timestamp: str, buffer_state: str, command: str, argument: str, response: str):
        command_output = "> {} [buffer: {}] {} {}\r\n".format(timestamp, buffer_state, command, argument)
        if not argument:
            command_output = "> {} [buffer: {}] {}\r\n".format(timestamp, buffer_state, command)

        self._f.write(command_output)


class ResponseLog(TransactionLog):
    def _write(self, timestamp: str, buffer_state: str, command: str, argument: str, response: str):
        response_output = "< {} (No response)".format(timestamp)
        if response:
            response_output = "< {} {}".format(timestamp, response)

        self._f.write(response_output)
