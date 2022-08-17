import unittest
from rsmtpd.core.validation import EmailAddressParseResult, EmailAddressVerificationResult
from rsmtpd.handlers.reset import ResetHandler
from rsmtpd.handlers.shared_state import SharedState
from tests.mocks import StubLoggerFactory, MockConfigLoader


class TestResetHandler(unittest.TestCase):
    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        self._mock_config_loader = MockConfigLoader(StubLoggerFactory())

    def test_handle(self):
        handler = ResetHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.mail_from = EmailAddressParseResult()
        shared_state.recipients = [EmailAddressVerificationResult(EmailAddressParseResult(), True)]
        shared_state.data_filename = "/var/tmp/rsmtpd-unit-test-test-filename"

        response = handler.handle("RESET", "", shared_state)

        self.assertIsNone(shared_state.mail_from)
        self.assertEqual(len(shared_state.recipients), 0)
        self.assertIsNone(shared_state.data_filename)
        self.assertEqual(response.get_code(), 250)


if __name__ == '__main__':
    unittest.main()
