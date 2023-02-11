import unittest
from rsmtpd.handlers.post_data_reset import PostDataResetDataHandler
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.smtp_552 import SmtpResponse552
from rsmtpd.validators.email_address.parser import ParsedEmailAddress
from rsmtpd.validators.email_address.recipient import ValidatedRecipient
from tests.mocks import StubLoggerFactory, MockConfigLoader


class TestPostDataResetDataHandlerDataHandler(unittest.TestCase):
    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        self._mock_config_loader = MockConfigLoader(StubLoggerFactory())

    def test_handle_data_and_data_end(self):
        handler = PostDataResetDataHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.mail_from = ParsedEmailAddress()
        shared_state.recipients = [ValidatedRecipient(ParsedEmailAddress(), True)]
        shared_state.data_filename = "/var/tmp/rsmtpd-unit-test-test-filename"

        handler.handle_data(b'', shared_state)

        self.assertIsNotNone(shared_state.mail_from)
        self.assertNotEqual(len(shared_state.recipients), 0)
        self.assertIsNotNone(shared_state.data_filename)

        shared_state.current_command.response = SmtpResponse552()
        response = handler.handle_data_end(shared_state)

        self.assertIsNone(shared_state.mail_from)
        self.assertEqual(len(shared_state.recipients), 0)
        self.assertIsNone(shared_state.data_filename)
        self.assertEqual(response.get_code(), 552)


if __name__ == '__main__':
    unittest.main()
