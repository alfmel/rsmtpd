from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse250(BaseResponse):
    _smtp_code = 250
    _message = "OK"
    _action = OK
