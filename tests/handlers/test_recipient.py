import unittest
from logging import Logger
from rsmtpd.core.validation import EmailAddressVerificationResult
from rsmtpd.handlers.recipient import RecipientHandler
from rsmtpd.handlers.shared_state import SharedState, ClientName
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestRecipientHandler(unittest.TestCase):
    _mock_logger: Logger

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)

    def test_no_helo(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        handler = RecipientHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("RCPT", "TO:<test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 503)
        self.assertEqual(len(shared_state.recipients), 0)

    def test_bad_argument(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("RCPT", "SEND:<test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 504)
        self.assertEqual(len(shared_state.recipients), 0)

    def test_handle(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("RCPT", "TO:<test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 250)
        recipient_list = list(shared_state.recipients)
        self.assertEqual(len(recipient_list), 1)
        self.assertIsInstance(recipient_list[0], EmailAddressVerificationResult)
        self.assertEqual(recipient_list[0].email_address, "test@example.com")

    def test_handle_no_bracket(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("RCPT", "to:test@example.com", shared_state)

        self.assertEqual(response.get_code(), 250)
        recipient_list = list(shared_state.recipients)
        self.assertIsInstance(recipient_list[0], EmailAddressVerificationResult)
        self.assertEqual(recipient_list[0].email_address, "test@example.com")

    def test_handle_multiple(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader)

        handler.handle("RCPT", "TO:<test1@example.com>", shared_state)
        response = handler.handle("RCPT", "TO:<test2@example.com>", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertEqual(len(shared_state.recipients), 2)

    def test_handle_duplicates(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader)

        handler.handle("RCPT", "TO:<test@example.com>", shared_state)
        response = handler.handle("RCPT", "TO:<Test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertEqual(len(shared_state.recipients), 1)


if __name__ == '__main__':
    unittest.main()
