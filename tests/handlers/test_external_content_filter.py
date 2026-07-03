import os
import tempfile
import unittest
from logging import Logger
from rsmtpd.handlers.external_content_filter import ExternalContentFilter
from rsmtpd.handlers.shared_state import SharedState, CurrentCommand
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.validators.email_address.parser import parse_email_address_input
from rsmtpd.validators.email_address.recipient import ValidatedRecipient
from tests.mocks import MockConfigLoader, StubLoggerFactory


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class TestExternalContentFilter(unittest.TestCase):
    _mock_logger: Logger
    _mock_config_loader: MockConfigLoader

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        self._mock_config_loader = MockConfigLoader(StubLoggerFactory())

    def test_email_rejected(self):
        shared_state = SharedState(("10.20.30.40", 12345))
        shared_state.mail_from = parse_email_address_input("<>", True)
        recipient = parse_email_address_input("<test@example.com>")
        recipient.email_address = "test@example.com"
        shared_state.recipients = {ValidatedRecipient(recipient, deliver_to="test.example.com")}
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        with tempfile.NamedTemporaryFile("wb", delete=False) as fp:
            shared_state.data_filename = fp.name
            fp.write(TEST_MESSAGE)

        config = {
            "command": os.path.join(DIR_PATH, "..", "helpers", "external_content_filter.sh") + " 10",
            "reject_threshold": 9,
            "flag_threshold": 6.5,
            "flags": [
                "Spam: Yes",
                "X-Spam: Yes"
            ]
        }

        handler = ExternalContentFilter(self._mock_logger, self._mock_config_loader, "", config)

        response = handler.handle_data_end(shared_state)

        self.assertEqual(response.get_code(), 550)

    def test_email_flagged(self):
        shared_state = SharedState(("10.20.30.40", 12345))
        shared_state.mail_from = parse_email_address_input("<>", True)
        recipient = parse_email_address_input("<test@example.com>")
        recipient.email_address = "test@example.com"
        shared_state.recipients = {ValidatedRecipient(recipient, deliver_to="test.example.com")}
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        with tempfile.NamedTemporaryFile("wb", delete=False) as fp:
            shared_state.data_filename = fp.name
            fp.write(TEST_MESSAGE)

        config = {
            "command": os.path.join(DIR_PATH, "..", "helpers", "external_content_filter.sh") + " 6.5",
            "reject_threshold": 9,
            "flag_threshold": 6.5,
            "flags": [
                "Spam: Yes",
                "X-Spam: Yes"
            ]
        }

        handler = ExternalContentFilter(self._mock_logger, self._mock_config_loader, "", config)

        response = handler.handle_data_end(shared_state)

        self.assertEqual(response.get_code(), 250)
        self.__assert_file_equals_and_delete(shared_state.data_filename, FLAGGED_TEST_MESSAGE)

    def test_email_passes(self):
        shared_state = SharedState(("10.20.30.40", 12345))
        shared_state.mail_from = parse_email_address_input("<>", True)
        recipient = parse_email_address_input("<test@example.com>")
        recipient.email_address = "test@example.com"
        shared_state.recipients = {ValidatedRecipient(recipient, deliver_to="test.example.com")}
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        with tempfile.NamedTemporaryFile("wb", delete=False) as fp:
            shared_state.data_filename = fp.name
            fp.write(TEST_MESSAGE)

        config = {
            "command": os.path.join(DIR_PATH, "..", "helpers", "external_content_filter.sh") + " 1",
            "reject_threshold": 9,
            "flag_threshold": 6.5,
            "flags": [
                "Spam: Yes",
                "X-Spam: Yes"
            ]
        }

        handler = ExternalContentFilter(self._mock_logger, self._mock_config_loader, "", config)

        response = handler.handle_data_end(shared_state)

        self.assertEqual(response.get_code(), 250)
        self.__assert_file_equals_and_delete(shared_state.data_filename, TEST_MESSAGE)

    def __assert_file_equals_and_delete(self, filename: str, expected_message: bytes):
        with open(filename, "rb") as file:
            message = file.read()

        os.unlink(filename)
        self.assertEqual(message, expected_message)


TEST_MESSAGE = \
    b"From: <test@example.com>\r\n" \
    b"To: <test@example.com>\r\n" \
    b"Subject: Some subject\r\n" \
    b"Date: Sat, 11 Feb 2023 12:00:00\r\n" \
    b"\r\n" \
    b"This is line one of the body.\r\n" \
    b"This is line two of the body followed by some empty lines.\r\n" \
    b"\r\n" \
    b"\r\n" \
    b"This is the last line of the body.\r\n"

FLAGGED_TEST_MESSAGE = \
    b"From: <test@example.com>\r\n" \
    b"To: <test@example.com>\r\n" \
    b"Subject: Some subject\r\n" \
    b"Date: Sat, 11 Feb 2023 12:00:00\r\n" \
    b"Spam: Yes\r\n" \
    b"X-Spam: Yes\r\n" \
    b"\r\n" \
    b"This is line one of the body.\r\n" \
    b"This is line two of the body followed by some empty lines.\r\n" \
    b"\r\n" \
    b"\r\n" \
    b"This is the last line of the body.\r\n"

if __name__ == '__main__':
    unittest.main()
