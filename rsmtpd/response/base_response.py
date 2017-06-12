from rsmtpd.response.action import OK


class BaseResponse(object):
    """
    Base SMTP response. All responses must extend this class.

    The class includes:

     - A numeric SMTP code
     - A message (can be overwritten during instantiation with the alt_message parameter)
     - A worker action (see rsmtpd.core.worker for details)

     The message may contain <domain> (including the diamonds) to insert the server's name as required by RFC 5321
     (notably SMTP codes 220, 221 and 421 [Section 4.2.3]).
    """

    _smtp_code = 0
    _message = None
    _action = OK

    def __init__(self, alt_message: str=None):
        """
        :param alt_message: Override the message, if desired (don't abuse)
        """
        if alt_message is not None and len(alt_message) > 0:
            self._message = alt_message

    def get_code(self) -> int:
        return self._smtp_code

    def get_message(self) -> str:
        return self._message

    def get_action(self) -> str:
        return self._action

    def get_smtp_response(self) -> str:
        return "{} {}\r\n".format(self._smtp_code, self._message)
