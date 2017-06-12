from rsmtpd.response.action import CLOSE, OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse521(BaseResponse):
    _smtp_code = 521
    _message = "Server does not accept mail"
    _action = CLOSE

    def __init__(self, alt_message: str=None, close_on_connect: bool=True):
        super().__init__(alt_message)

        if not close_on_connect:
            self._action = OK
