from rsmtpd.response.action import CLOSE
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse221(BaseResponse):
    _smtp_code = 221
    _message = "<domain> Service closing transmission channel"
    _action = CLOSE
