import re
from copy import deepcopy
from rsmtpd.handlers.base_data_command import BaseDataCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from typing import List

from rsmtpd.response.smtp_550 import SmtpResponse550


class UndeliverableNotificationValidator(BaseDataCommand):
    __UNDELIVERABLE_EXPRESSIONS = [
        re.compile(b"daemon", re.IGNORECASE),
        re.compile(b"error", re.IGNORECASE),
        re.compile(b"failed", re.IGNORECASE),
        re.compile(b"server", re.IGNORECASE),
        re.compile(b"status", re.IGNORECASE),
        re.compile(b"system", re.IGNORECASE),
        re.compile(b"undeliverable", re.IGNORECASE),
        re.compile(b"deliver", re.IGNORECASE),
    ]

    def handle_data(self, data: bytes, shared_state: SharedState):
        pass

    def handle_data_end(self, shared_state: SharedState) -> BaseResponse:
        if shared_state.mail_from.email_address == "" and shared_state.data_filename:
            try:
                expressions_found = 0
                expressions_left = deepcopy(self.__UNDELIVERABLE_EXPRESSIONS)

                with open(shared_state.data_filename, "rb") as file:
                    for line in file:
                        count, expressions = self.__count_and_reduce_matching_expressions(line, expressions_left)
                        expressions_found += count

                if expressions_found < 3:
                    self._logger.error(f"Rejecting message to {shared_state.transaction_id}: "
                                       f"message had empty MAIL FROM but only {expressions} undeliverable expressions "
                                       f"in body")
                    return SmtpResponse550("Message does not appear to contain a Undeliverable Mail Notification",
                                           ["Message does not appear to contain a Undeliverable Mail Notification",
                                            "We hae considered this message to be Spam and will not be delivered"
                                            "Remove this recipient and others in this domain from your lists"])

            except Exception:
                pass

        return shared_state.current_command.response

    def __count_and_reduce_matching_expressions(self, line: bytes, expressions: List) -> (int, List):
        count = 0
        expressions_left = []
        for expression in expressions:
            if expression.search(line):
                count += 1
            else:
                expressions_left.append(expression)

        return count, expressions_left
