import unittest
from logging import Logger
from rsmtpd.core.validation import EmailAddressParseResult
from rsmtpd.handlers.mail import MailHandler
from rsmtpd.handlers.shared_state import SharedState, ClientName
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestMailHandler(unittest.TestCase):
    _mock_logger: Logger

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)

    def test_no_helo(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        handler = MailHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("MAIL", "FROM:<test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 503)
        self.assertIsNone(shared_state.mail_from)

    def test_bad_argument(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = MailHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("MAIL", "SEND:<test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 504)
        self.assertIsNone(shared_state.mail_from)

    def test_handle(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = MailHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("MAIL", "FROM:<test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertIsInstance(shared_state.mail_from, EmailAddressParseResult)
        self.assertEqual(shared_state.mail_from.email_address, "test@example.com")

    def test_handle_no_bracket(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = MailHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("MAIL", "FROM:test@example.com", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertIsInstance(shared_state.mail_from, EmailAddressParseResult)
        self.assertEqual(shared_state.mail_from.email_address, "test@example.com")


if __name__ == '__main__':
    unittest.main()
