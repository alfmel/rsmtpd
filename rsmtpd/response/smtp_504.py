from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse504(BaseResponse):
    _smtp_code = 504
    _message = "Command parameter not implemented"
    _action = OK
