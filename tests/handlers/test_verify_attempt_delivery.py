import unittest
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.handlers.verify_attempt_delivery import VerifyAttemptDeliveryHandler
from tests.mocks import StubLoggerFactory, MockConfigLoader


class TestVerifyAttemptDeliveryHandler(unittest.TestCase):
    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        self._mock_config_loader = MockConfigLoader(StubLoggerFactory())

    def test_handle(self):
        handler = VerifyAttemptDeliveryHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))

        response = handler.handle("VRFY", "", shared_state)

        self.assertEqual(response.get_code(), 252)


if __name__ == '__main__':
    unittest.main()
