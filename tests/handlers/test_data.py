import unittest
from logging import Logger

from rsmtpd.core.validation import EmailAddressParseResult, EmailAddressVerificationResult
from rsmtpd.handlers.data import DataHandler
from rsmtpd.handlers.shared_state import SharedState
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestDataHandler(unittest.TestCase):
    _mock_logger: Logger
    _mock_config_loader: MockConfigLoader

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        self._mock_config_loader = MockConfigLoader(StubLoggerFactory())

    def test_with_argument(self):
        handler = DataHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))

        response = handler.handle("DATA", "some argument", shared_state)
        self.assertEqual(response.get_code(), 501)

    def test_no_helo(self):
        handler = DataHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))

        response = handler.handle("DATA", "", shared_state)
        self.assertEqual(response.get_code(), 503)
        self.assertTrue("EHLO" in response.get_smtp_response())

    def test_no_mail_from(self):
        handler = DataHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = "localhost"

        response = handler.handle("DATA", "", shared_state)
        self.assertEqual(response.get_code(), 503)
        self.assertTrue("MAIL" in response.get_smtp_response())

    def test_no_recipients(self):
        handler = DataHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = "localhost"
        shared_state.mail_from = EmailAddressParseResult()

        response = handler.handle("DATA", "", shared_state)
        self.assertEqual(response.get_code(), 503)
        self.assertTrue("recipients" in response.get_smtp_response())

    def test_everything_read(self):
        handler = DataHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.client_name = "localhost"
        shared_state.mail_from = EmailAddressParseResult()
        recipient = EmailAddressParseResult()
        recipient.email_address = "test@example.com"
        shared_state.recipients.add(EmailAddressVerificationResult(recipient))

        response = handler.handle("DATA", "", shared_state)
        self.assertEqual(response.get_code(), 354)


if __name__ == '__main__':
    unittest.main()
