from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse500(BaseResponse):
    _smtp_code = 500
    _message = "Syntax error, command unrecognized"
    _action = OK
