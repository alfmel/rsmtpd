import os
import shutil
import subprocess
from rsmtpd.handlers.base_data_command import BaseDataCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_550 import SmtpResponse550
from typing import List


class ExternalContentFilter(BaseDataCommand):
    """
    This module will execute the given command and pass a reference to the message data file as the last argument. It
    expects output with a number representing a score of whether the message is spam or not. If the number is above the
    threshold set in the configuration, the server will reject the email.
    """

    def handle_data(self, data: bytes, shared_state: SharedState):
        pass

    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        if not self._config.get("command"):
            self._logger.warning("External content filter command is missing; no content filter will be done")
            return shared_state.current_command.response

        if not shared_state.data_filename or \
                not shared_state.current_command.response or \
                shared_state.current_command.response.get_code() != 250:
            self._logger.info("Content filter skipped as there is nothing to filter")
            return shared_state.current_command.response

        try:
            command = self._config.get("command", "")
            reject_threshold = self._config.get("reject_threshold", 1e12)  # Don't reject or flag if value is missing
            flag_threshold = self._config.get("flag_threshold", 1e12)
            flags = self._config.get("flags", [])

            command_list = command if isinstance(command, list) else command.split(" ")
            command_list.append(shared_state.data_filename)

            result = subprocess.run(command_list, capture_output=True)
            if result.returncode != 0:
                self._logger.error(f"External content filter exited with return code {result.returncode}")
                return shared_state.current_command.response

            output = result.stdout.decode("utf-8").strip()
            value = float(output)
            self._logger.info(f"Message {shared_state.transaction_id} received external content filter score of "
                              f"{value} (flag threshold {flag_threshold} / reject threshold {reject_threshold})")

            if value >= reject_threshold:
                self._logger.warning(f"Message {shared_state.transaction_id} received score of {value} from external "
                                     f"content filter and it is being rejected (threshold: {reject_threshold})")
                return SmtpResponse550("The content of message suggests this email is Spam")

            if value >= flag_threshold:
                self._logger.warning(f"Message {shared_state.transaction_id} received score of {value} from external "
                                     f"content filter and it is being flagged (threshold: {flag_threshold})")
                self._flag_message(shared_state.data_filename, flags)
        except ValueError:
            self._logger.error("External content filter command did not returned a numeric value; ignoring result")
        except Exception as e:
            self._logger.error("Error executing external content filter command: message will not be rejected or "
                               "flagged", e)

        return shared_state.current_command.response

    def _flag_message(self, filename: str, flags: List[str]):
        try:
            untagged_filename = f"{filename}--untagged"
            shutil.copy(filename, untagged_filename)

            flags_inserted = False

            with open(untagged_filename, "rb") as input_file:
                with open(filename, "wb") as output_file:
                    for line in input_file:
                        if not flags_inserted and line == b"\r\n" or line == b"\n":
                            for flag in flags:
                                output_file.write(bytes(flag, "UTF-8") + b"\r\n")
                            flags_inserted = True
                        output_file.write(line)

                    if not flags_inserted:
                        for flag in flags:
                            output_file.write(bytes(flag, "UTF-8") + b"\r\n")

            os.remove(untagged_filename)
        except Exception as e:
            self._logger.error("Unable to tag message", e)
            pass
