from unittest import TestCase

from rsmtpd.response.action import OK
from rsmtpd.response.base_response import BaseResponse


class TestResponse(TestCase):
    """
    Unit tests for single and multi-line responses
    """

    def testSingleLineResponse(self):
        response = SingleLineResponse()
        self.assertEqual(response.get_smtp_response(),
                         "{} {}\r\n".format(response.get_code(), response.get_message()))

        response = MultiLineResponse()
        self.assertEqual(response.get_smtp_response(),
                         "{} {}\r\n".format(response.get_code(), response.get_message()))

    def testMultiLineResponse(self):
        response = SingleLineResponse()
        self.assertEqual(response.get_extended_smtp_response(),
                         "{} {}\r\n".format(response.get_code(), response.get_message()))
        response = MultiLineResponse()
        self.assertEqual(response.get_extended_smtp_response(),
                         "{}-{}\r\n{}-{}\r\n{} {}\r\n".format(response.get_code(), response.get_multi_line_message()[0],
                                                              response.get_code(), response.get_multi_line_message()[1],
                                                              response.get_code(), response.get_multi_line_message()[2])
                         )


class SingleLineResponse(BaseResponse):
    _smtp_code = 789
    _message = "Some really cool response message"
    _action = OK


class MultiLineResponse(BaseResponse):
    _smtp_code = 789
    _message = "Some really cool response message"
    _multi_line_message = ["This is line 1",
                           "This is line 2",
                           "And this is line 3 of a multi-line response"]
    _action = OK
