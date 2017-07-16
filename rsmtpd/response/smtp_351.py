from rsmtpd.response.action import CONTINUE
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse351(BaseResponse):
    _smtp_code = 351
    _message = "Start mail input; end with <CRLF>.<CRLF>"
    _action = CONTINUE

    def __init__(self, alt_message: str=None):
        super().__init__(alt_message)
