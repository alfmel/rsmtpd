import unittest
from logging import Logger
from rsmtpd.handlers.greeting import GreetingHandler
from rsmtpd.handlers.shared_state import SharedState
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestGreetingHandler(unittest.TestCase):
    """
    Unit test for the Greeting command handler
    """

    _mock_logger: Logger

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)

    def test_no_config(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        handler = GreetingHandler(self._mock_logger, mock_config_loader)

        shared_state = SharedState(("1.2.3.4", 12345))
        response = handler.handle("", "", shared_state)

        self.assertEqual(response.get_code(), 220)
        self.assertNotEqual(response.get_message(), "")

    def test_with_message(self):
        message = "Test greeting message"
        mock_config_loader = MockConfigLoader(StubLoggerFactory(), {"message": message})
        handler = GreetingHandler(self._mock_logger, mock_config_loader)

        shared_state = SharedState(("1.2.3.4", 12345))
        response = handler.handle("", "", shared_state)

        self.assertEqual(response.get_code(), 220)
        self.assertEqual(response.get_message(), message)


if __name__ == '__main__':
    unittest.main()
