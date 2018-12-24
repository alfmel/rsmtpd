from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse501(BaseResponse):
    _smtp_code = 501
    _message = "Syntax error in parameters or arguments"
    _action = OK
