import os
import tempfile
import unittest
from logging import Logger

from rsmtpd.handlers.shared_state import SharedState, CurrentCommand
from rsmtpd.handlers.undeliverable_notification_validator import UndeliverableNotificationValidator
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.validators.email_address.parser import parse_email_address_input
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestUndeliverableNotificationValidator(unittest.TestCase):
    _mock_logger: Logger
    _mock_config_loader: MockConfigLoader

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        self._mock_config_loader = MockConfigLoader(StubLoggerFactory())

    def test_email_is_undeliverable_notification(self):
        shared_state = SharedState(("10.20.30.40", 12345))
        shared_state.mail_from = parse_email_address_input("<>", True)
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        with tempfile.NamedTemporaryFile("wb", delete=False) as fp:
            shared_state.data_filename = fp.name
            fp.write(b"From: <test@example.com>\r\n")
            fp.write(b"To: <test@example.com>\r\n")
            fp.write(b"Subject: Message undeliverable\r\n")
            fp.write(b"Date: Sat, 11 Feb 2023 12:00:00\r\n")
            fp.write(b"\r\n")
            fp.write(b"There was an error and your message delivering your message.\r\n")
            fp.write(b"This is a permanent error status.\r\n")

        handler = UndeliverableNotificationValidator(self._mock_logger, self._mock_config_loader)
        response = handler.handle_data_end(shared_state)
        os.unlink(shared_state.data_filename)

        self.assertEqual(response.get_code(), 250)

    def test_email_is_spam(self):
        shared_state = SharedState(("10.20.30.40", 12345))
        shared_state.mail_from = parse_email_address_input("<>", True)
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        with tempfile.NamedTemporaryFile("wb", delete=False) as fp:
            shared_state.data_filename = fp.name
            fp.write(b"From: <test@example.com>\r\n")
            fp.write(b"To: <test@example.com>\r\n")
            fp.write(b"Subject: Some stupid subject line\r\n")
            fp.write(b"Date: Sat, 11 Feb 2023 12:00:00\r\n")
            fp.write(b"\r\n")
            fp.write(b"This is some text about some product you don't want to buy!!!\r\n")
            fp.write(b"I mean, why wouldn't you want this product now!?\r\n")

        handler = UndeliverableNotificationValidator(self._mock_logger, self._mock_config_loader)
        response = handler.handle_data_end(shared_state)
        os.unlink(shared_state.data_filename)

        self.assertEqual(response.get_code(), 550)


if __name__ == '__main__':
    unittest.main()
