from logging import Logger
from unittest import TestCase
from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.handlers.quit import Quit
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.smtp_221 import SmtpResponse221
from rsmtpd.response.smtp_501 import SmtpResponse501
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestQuitHandler(TestCase):
    """
    Unit test for the Quit command handler
    """

    _mockLogger: Logger
    _mockConfigLoader: ConfigLoader
    _shared_state: SharedState

    def setUp(self):
        stub_logger_factory = StubLoggerFactory()
        self._shared_state = SharedState(("1.2.3.4", 12345))
        self._mockLogger = stub_logger_factory.get_module_logger(None)
        self._mockConfigLoader = MockConfigLoader(stub_logger_factory)

    def testHandleNoArgument(self):
        handler = Quit(self._mockLogger, self._mockConfigLoader)
        response = handler.handle("QUIT", "", self._shared_state)
        self.assertIsInstance(response, SmtpResponse221)

    def testHandleWithArgument(self):
        handler = Quit(self._mockLogger, self._mockConfigLoader)
        response = handler.handle("QUIT", "now", self._shared_state)
        self.assertIsInstance(response, SmtpResponse501)
