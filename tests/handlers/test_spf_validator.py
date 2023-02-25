import unittest
from logging import Logger

from rsmtpd.handlers.shared_state import SharedState, CurrentCommand, ClientName
from rsmtpd.handlers.spf_validator import SpfValidator
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.response.smtp_550 import SmtpResponse550
from rsmtpd.validators.email_address.parser import parse_email_address_input
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestSpfValidator(unittest.TestCase):
    _mock_logger: Logger
    _mock_config_loader: MockConfigLoader

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        self._mock_config_loader = MockConfigLoader(StubLoggerFactory())

    def test_spf_no_response(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("mail.example.com")
        shared_state.mail_from = parse_email_address_input("<test@example.com>")
        shared_state.current_command = CurrentCommand()

        handler = SpfValidator(self._mock_logger, self._mock_config_loader)

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertIsNone(response)

    def test_spf_no_250_response(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("mail.example.com")
        shared_state.mail_from = parse_email_address_input("<test@example.com>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse550()

        handler = SpfValidator(self._mock_logger, self._mock_config_loader)

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 550)

    def test_spf_empty_mail_from(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("mail.example.com")
        shared_state.mail_from = parse_email_address_input("<>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = SpfValidator(self._mock_logger, self._mock_config_loader)

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 250)

    def test_spf_pass(self):
        shared_state = SharedState(("192.30.252.201", 54321))  # IP address allowed by GitHub SPF policy
        shared_state.client_name = ClientName("out-18.smtp.github.com")
        shared_state.mail_from = parse_email_address_input("<noreply@github.com>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = SpfValidator(self._mock_logger, self._mock_config_loader)

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 250)

    def test_spf_fail(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("mail.example.com")
        shared_state.mail_from = parse_email_address_input("<test@example.com>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = SpfValidator(self._mock_logger, self._mock_config_loader)

        response = handler.handle("MAIL", "FROM", shared_state)

        self.assertEqual(response.get_code(), 550)
        self.assertFalse(shared_state.mail_from.is_valid)


if __name__ == '__main__':
    unittest.main()
