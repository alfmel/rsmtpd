import unittest

from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.handlers.starttls import StartTLS
from tests.mocks import StubLoggerFactory, MockConfigLoader


class TestStartTLS(unittest.TestCase):
    def setUp(self):
        self._stub_logger_factory = StubLoggerFactory()
        self._mock_logger = self._stub_logger_factory.get_module_logger(None)
        self._mockConfigLoader = MockConfigLoader(self._stub_logger_factory)

    def test_tls_not_available(self):
        shared_state = SharedState(("1.2.3.4", 12345), False)
        handler = StartTLS(self._mock_logger, self._mockConfigLoader)
        response = handler.handle("STARTTLS", "", shared_state)
        self.assertEqual(response.get_code(), 500)

    def test_tls_available(self):
        shared_state = SharedState(("1.2.3.4", 12345), True)
        handler = StartTLS(self._mock_logger, self._mockConfigLoader)
        response = handler.handle("STARTTLS", "", shared_state)
        self.assertEqual(response.get_code(), 220)

    def test_tls_available_already_started(self):
        shared_state = SharedState(("1.2.3.4", 12345), True)
        shared_state.client.tls_enabled = True
        handler = StartTLS(self._mock_logger, self._mockConfigLoader)
        response = handler.handle("STARTTLS", "", shared_state)
        self.assertEqual(response.get_code(), 503)


if __name__ == '__main__':
    unittest.main()
