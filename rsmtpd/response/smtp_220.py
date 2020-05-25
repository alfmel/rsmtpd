from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse220(BaseResponse):
    _smtp_code = 220
    _message = "<domain> Service ready"
    _action = OK
