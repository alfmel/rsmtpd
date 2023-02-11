from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse450(BaseResponse):
    _smtp_code = 450
    _message = "Mailbox unavailable; please try again later"
    _action = OK

    def __init__(self, alt_message: str = None):
        super().__init__(alt_message)
