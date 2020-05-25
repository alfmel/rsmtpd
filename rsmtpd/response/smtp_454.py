from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse454(BaseResponse):
    _smtp_code = 454
    _message = "TLS failed"
    _action = OK

    def __init__(self, alt_message: str = None):
        super().__init__(alt_message)
