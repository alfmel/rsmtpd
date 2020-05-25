from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse503(BaseResponse):
    _smtp_code = 503
    _message = "Bad sequence of commands"
    _action = OK
