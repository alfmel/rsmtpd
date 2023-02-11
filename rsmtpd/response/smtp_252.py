from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse252(BaseResponse):
    _smtp_code = 252
    _message = "Cannot VRFY user, but will accept message and attempt delivery"
    _action = OK
