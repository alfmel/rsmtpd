import unittest
from logging import Logger
from rsmtpd.handlers.recipient import RecipientHandler
from rsmtpd.handlers.shared_state import SharedState, ClientName
from rsmtpd.validators.email_address.recipient import ValidatedRecipient
from rsmtpd.validators.email_address.simple_recipient_validator import SimpleRecipientValidator
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestRecipientHandler(unittest.TestCase):
    _mock_logger: Logger

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        validator_config = {
            "allow_soft_delivery": False,
            "allow_tagging": False,
            "domains": {"example.com": {"recipients": ["test", "test1", "test2"]}}
        }
        self._recipient_validator = SimpleRecipientValidator(self._mock_logger, MockConfigLoader(StubLoggerFactory()),
                                                             "", validator_config)

    def test_no_helo(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        handler = RecipientHandler(self._mock_logger, mock_config_loader, "", {}, self._recipient_validator)

        response = handler.handle("RCPT", "TO:<test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 503)
        self.assertEqual(len(shared_state.recipients), 0)

    def test_bad_argument(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader, "", {}, self._recipient_validator)

        response = handler.handle("RCPT", "SEND:<test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 504)
        self.assertEqual(len(shared_state.recipients), 0)

    def test_handle(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader, "", {}, self._recipient_validator)

        response = handler.handle("RCPT", "TO:<test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 250)
        recipient_list = list(shared_state.recipients)
        self.assertEqual(len(recipient_list), 1)
        self.assertIsInstance(recipient_list[0], ValidatedRecipient)
        self.assertEqual(recipient_list[0].email_address, "test@example.com")

    def test_handle_no_bracket(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader, "", {}, self._recipient_validator)

        response = handler.handle("RCPT", "to:test@example.com", shared_state)

        self.assertEqual(response.get_code(), 250)
        recipient_list = list(shared_state.recipients)
        self.assertIsInstance(recipient_list[0], ValidatedRecipient)
        self.assertEqual(recipient_list[0].email_address, "test@example.com")

    def test_handle_multiple_recipients(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader, "", {}, self._recipient_validator)

        handler.handle("RCPT", "TO:<test1@example.com>", shared_state)
        response = handler.handle("RCPT", "TO:<test2@example.com>", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertEqual(len(shared_state.recipients), 2)

    def test_handle_duplicates(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = ClientName()
        handler = RecipientHandler(self._mock_logger, mock_config_loader, "", {}, self._recipient_validator)

        handler.handle("RCPT", "TO:<test@example.com>", shared_state)
        response = handler.handle("RCPT", "TO:<Test@example.com>", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertEqual(len(shared_state.recipients), 1)


if __name__ == '__main__':
    unittest.main()
