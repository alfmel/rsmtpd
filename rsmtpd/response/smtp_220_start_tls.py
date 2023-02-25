from rsmtpd.response.action import STARTTLS
from rsmtpd.response.base_response import BaseResponse


class SmtpResponse220StartTLS(BaseResponse):
    _smtp_code = 220
    _message = "Ready to start TLS"
    _action = STARTTLS
