from rsmtpd.response.action import INVALID, OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse451(BaseResponse):
    _smtp_code = 451
    _message = "Requested action aborted: local error in processing"
    _action = INVALID

    def __init__(self, alt_message: str=None, permanent=False):
        super().__init__(alt_message)

        if not permanent:
            self._action = OK
