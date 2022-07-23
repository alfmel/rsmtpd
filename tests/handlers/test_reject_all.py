from logging import Logger
from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.core.logger_factory import LoggerFactory
from rsmtpd.handlers.reject_all import RejectAll
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.action import CLOSE, OK, CONTINUE
from rsmtpd.response.smtp_354 import SmtpResponse354
from rsmtpd.response.smtp_521 import SmtpResponse521
from tests.mocks import MockConfigLoader, StubLoggerFactory
from unittest import TestCase


class TestRejectAllHandler(TestCase):
    """
    Unit test for the Reject All command handler
    """

    _stub_logger_factor: LoggerFactory
    _mockLogger: Logger
    _mockConfigLoader: ConfigLoader
    _shared_state: SharedState

    def setUp(self):
        self._stub_logger_factory = StubLoggerFactory()
        self._shared_state = SharedState(("1.2.3.4", 12345))
        self._mockLogger = self._stub_logger_factory.get_module_logger(None)

    def testHandleWithClose(self):
        self._mockConfigLoader = MockConfigLoader(self._stub_logger_factory)
        handler = RejectAll(self._mockLogger, self._mockConfigLoader)
        response = handler.handle("ANY", "thing", self._shared_state)
        self.assertIsInstance(response, SmtpResponse521)
        self.assertEqual(response.get_action(), CLOSE)

    def testHandleWithoutClose(self):
        self._mockConfigLoader = MockConfigLoader(self._stub_logger_factory, {"close_connection": False})
        handler = RejectAll(self._mockLogger, self._mockConfigLoader)
        response = handler.handle("RCPT", "TO", self._shared_state)
        self.assertIsInstance(response, SmtpResponse521)
        self.assertEqual(response.get_action(), OK)

    def testHandleWithoutCloseOnData(self):
        self._mockConfigLoader = MockConfigLoader(self._stub_logger_factory, {"close_connection": False})
        handler = RejectAll(self._mockLogger, self._mockConfigLoader)
        response = handler.handle("DATA", "", self._shared_state)
        self.assertIsInstance(response, SmtpResponse354)
        self.assertEqual(response.get_action(), CONTINUE)

    def testHandleDataEnd(self):
        self._mockConfigLoader = MockConfigLoader(self._stub_logger_factory, {"close_connection": False})
        handler = RejectAll(self._mockLogger, self._mockConfigLoader)
        response = handler.handle_data_end(self._shared_state)
        self.assertIsInstance(response, SmtpResponse521)
        self.assertEqual(response.get_action(), OK)
