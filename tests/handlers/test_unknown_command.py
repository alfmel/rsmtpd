from logging import Logger
from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.core.logger_factory import LoggerFactory
from rsmtpd.handlers.unknown_command import UnknownCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.action import CLOSE, OK, CONTINUE
from rsmtpd.response.smtp_500 import SmtpResponse500
from tests.mocks import MockConfigLoader, StubLoggerFactory
from unittest import TestCase


class TestRejectAllHandler(TestCase):
    """
    Unit test for the Unknown Command handler
    """

    _stub_logger_factor: LoggerFactory
    _mockLogger: Logger
    _mockConfigLoader: ConfigLoader
    _shared_state: SharedState

    def setUp(self):
        self._stub_logger_factory = StubLoggerFactory()
        self._shared_state = SharedState(("1.2.3.4", 12345))
        self._mockLogger = self._stub_logger_factory.get_module_logger(None)

    def testHandleNoArgument(self):
        self._mockConfigLoader = MockConfigLoader(self._stub_logger_factory)
        handler = UnknownCommand(self._mockLogger, self._mockConfigLoader)
        response = handler.handle("ANY", "", self._shared_state)
        self.assertIsInstance(response, SmtpResponse500)
        self.assertEqual(response.get_action(), OK)

    def testHandleWithArgument(self):
        self._mockConfigLoader = MockConfigLoader(self._stub_logger_factory)
        handler = UnknownCommand(self._mockLogger, self._mockConfigLoader)
        response = handler.handle("ANY", "thing", self._shared_state)
        self.assertIsInstance(response, SmtpResponse500)
        self.assertEqual(response.get_action(), OK)
