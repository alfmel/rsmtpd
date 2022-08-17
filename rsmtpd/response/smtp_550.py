from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse550(BaseResponse):
    _smtp_code = 550
    _message = "Invalid"
    _action = OK
