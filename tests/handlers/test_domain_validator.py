from logging import Logger
from unittest import TestCase

from rsmtpd.handlers.domain_validator import DomainValidator
from rsmtpd.handlers.shared_state import SharedState, ClientName, CurrentCommand
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.validators.email_address.parser import parse_email_address_input
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestDomainValidator(TestCase):
    _mock_logger: Logger
    _mock_config_loader: MockConfigLoader

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        self._mock_config_loader = MockConfigLoader(StubLoggerFactory())

    def test_invalid_client_name(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("some-client")
        shared_state.mail_from = parse_email_address_input("<test@example.com>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = DomainValidator(self._mock_logger, self._mock_config_loader)

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 550)

    def test_block_domain_list(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("mx.yahoo.com")
        shared_state.client_name.is_valid_fqdn = True
        shared_state.mail_from = parse_email_address_input("<user@yahoo.com>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = DomainValidator(self._mock_logger, self._mock_config_loader, "",
                                  {"domains_to_block": ["yahoo.com"]})

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 550)

    def test_block_domain_list_subdomain(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("mx.yahoo.com")
        shared_state.client_name.is_valid_fqdn = True
        shared_state.mail_from = parse_email_address_input("<user@corporate.yahoo.com>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = DomainValidator(self._mock_logger, self._mock_config_loader, "",
                                  {"domains_to_block": ["yahoo.com"]})

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 550)

    def test_block_domain_list_substring(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("mx.yahoo.com")
        shared_state.client_name.is_valid_fqdn = True
        shared_state.mail_from = parse_email_address_input("<user@yahoo.com>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = DomainValidator(self._mock_logger, self._mock_config_loader, "",
                                  {"domains_to_block": ["hoo.com"]})

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 250)

    def test_domain_too_new(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("mail.example.com")
        shared_state.client_name.is_valid_fqdn = True
        shared_state.mail_from = parse_email_address_input("<test@example.com>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = DomainValidator(self._mock_logger, self._mock_config_loader, "",
                                  {"minimum_domain_age_in_days": 36500})

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 550)

    def test_no_mx_records(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("mail.non-existent-domain.net")
        shared_state.client_name.is_valid_fqdn = True
        shared_state.mail_from = parse_email_address_input("<test@non-existent-domain.net>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = DomainValidator(self._mock_logger, self._mock_config_loader)

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 550)

    # Skipping for now as the client is not working
    # def test_bad_mx_server(self):
    #     # This test might fail if nowhere.com decides to start receiving email
    #     shared_state = SharedState(("10.20.30.40", 54321))
    #     shared_state.client_name = ClientName("mail.nowhere.com")
    #     shared_state.client_name.is_valid_fqdn = True
    #     shared_state.mail_from = parse_email_address_input("<nobody@nowhere.com>")
    #     shared_state.current_command = CurrentCommand()
    #     shared_state.current_command.response = SmtpResponse250()
    #
    #     handler = DomainValidator(self._mock_logger, self._mock_config_loader, "",
    #                               {"check_smtp_server_available": True})
    #
    #     response = handler.handle("MAIL", "FROM", shared_state)
    #     self.assertEqual(response.get_code(), 550)

    def test_domain_is_valid(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("smtp.gmail.com")
        shared_state.client_name.is_valid_fqdn = True
        shared_state.mail_from = parse_email_address_input("<some-user@gmail.com>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = DomainValidator(self._mock_logger, self._mock_config_loader, "",
                                  {"minimum_domain_age_in_days": 30, "check_smtp_server_available": False})  # TODO:True

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 250)

    def test_domain_is_valid_no_recipient(self):
        shared_state = SharedState(("10.20.30.40", 54321))
        shared_state.client_name = ClientName("smtp.gmail.com")
        shared_state.client_name.is_valid_fqdn = True
        shared_state.mail_from = parse_email_address_input("<>")
        shared_state.current_command = CurrentCommand()
        shared_state.current_command.response = SmtpResponse250()

        handler = DomainValidator(self._mock_logger, self._mock_config_loader, "",
                                  {"minimum_domain_age_in_days": 30, "check_smtp_server_available": False})  # TODO:True

        response = handler.handle("MAIL", "FROM", shared_state)
        self.assertEqual(response.get_code(), 250)
