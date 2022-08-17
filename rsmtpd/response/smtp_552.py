from rsmtpd.response.action import CLOSE, OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse552(BaseResponse):
    _smtp_code = 552
    _message = "Data rejected: message size exceeded"
    _action = CLOSE

    def __init__(self, alt_message: str = None, close_on_connect: bool = True):
        super().__init__(alt_message)

        if not close_on_connect:
            self._action = OK
