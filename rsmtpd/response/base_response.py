from typing import List

from rsmtpd.response.action import OK


class BaseResponse(object):
    """
    Base SMTP response. All responses must extend this class.

    The class includes:

     - A numeric SMTP code
     - A single-line message (can be overridden during instantiation with the alt_message parameter)
     - An optional multi-line message as a list of strings (one per line, overridden with alt_multi_line_message param)
     - A worker action (see rsmtpd.core.worker for details)

     The message may contain <server_name> (including the diamonds) to insert the server's name as required by RFC 5321
     (notably SMTP codes 220, 221 and 421 [Section 4.2.3]).
    """

    _smtp_code = 0
    _message = None
    _multi_line_message = None
    _action = OK

    def __init__(self, alt_message: str = None, alt_multi_line_message: List[str] = None):
        """
        :param alt_message: Override the message, if desired (don't abuse)
        :param alt_multi_line_message: Override multi-line message, if desired (don't abuse)
        """
        if alt_message is not None and len(alt_message) > 0:
            self._message = alt_message
        if alt_multi_line_message is not None and len(alt_multi_line_message) > 0:
            self._multi_line_message = alt_multi_line_message

    def get_code(self) -> int:
        return self._smtp_code

    def get_message(self) -> str:
        return self._message

    def get_multi_line_message(self) -> List[str]:
        return self._multi_line_message

    def get_action(self) -> str:
        return self._action

    def get_smtp_response(self) -> str:
        return "{} {}\r\n".format(self._smtp_code, self._message)

    def get_extended_smtp_response(self) -> str:
        if isinstance(self._multi_line_message, list) and len(self._multi_line_message) > 0:
            response = ""
            for index, line in enumerate(self._multi_line_message):
                response_format = "{}-{}\r\n"
                if index + 1 == len(self._multi_line_message):
                    response_format = "{} {}\r\n"

                response += response_format.format(self._smtp_code, line)

            return response
        else:
            return self.get_smtp_response()
