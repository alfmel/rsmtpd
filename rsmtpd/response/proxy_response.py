from typing import List

from rsmtpd.response.base_response import BaseResponse


class ProxyResponse(BaseResponse):
    _smtp_code = 0
    _message = None
    _multi_line_message = None

    def __init__(self, smtp_code: int, message: str = None, multi_line_message: List[str] = None):
        super().__init__(message, multi_line_message)
        self._smtp_code = smtp_code
