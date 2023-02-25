from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_550 import SmtpResponse550
from rsmtpd.validators.domain import dns
from smtplib import SMTP
from typing import List


class DomainValidator(BaseCommand):
    """
    Verifies the host can receive email and optionally that is not too old
    """

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if not shared_state.current_command.response or shared_state.current_command.response.get_code() != 250:
            self._logger.warning("Skipping domain validation: previous response not 250")
            return shared_state.current_command.response

        verify_smtp_server_available = self._config.get("verify_smtp_server_available", False)
        minimum_domain_age_in_days = self._config.get("minimum_domain_age_in_days", 0)
        domains_to_block = self._config.get("domains_to_block", [])

        domain = shared_state.mail_from.domain or self.__get_domain(shared_state.client_name.name)

        if not shared_state.client_name.is_valid_fqdn:
            self._logger.warning("Rejecting sender as client did not present a valid name")
            return SmtpResponse550(f"We are not accepting emails from {domain} at this time")

        for domain_to_block in domains_to_block:
            if domain == domain_to_block or domain.endswith(f".{domain_to_block}"):
                self._logger.warning("Rejecting sender as domain is in block domain list")
                return SmtpResponse550(f"We are not accepting emails from {domain} at this time")

        domain_age = dns.get_domain_age_in_days(domain)
        if domain_age < minimum_domain_age_in_days:
            self._logger.warning(f"Rejecting sender as domain has age of {domain_age} days "
                                 f"({minimum_domain_age_in_days} required)")
            return SmtpResponse550(f"We are not accepting emails from {domain} at this time")

        domain_mx_records = dns.mx_records(domain)
        if len(domain_mx_records) == 0:
            self._logger.warning("Rejecting sender as domain does not have MX records")
            return SmtpResponse550(f"We are not accepting emails from {domain} at this time")

        if verify_smtp_server_available and not self.__is_smtp_server_available(domain_mx_records):
            self._logger.warning("Rejecting sender as SMTP server does not accept email")
            return SmtpResponse550(f"We are not accepting emails from {domain} at this time")

        return shared_state.current_command.response

    def __get_domain(self, domain: str) -> str:
        if domain.count(".") > 1:
            return domain[domain.find(".") + 1:]

        return domain

    def __is_smtp_server_available(self, mx_servers: List[str]) -> bool:
        for mx_server in mx_servers:
            try:
                with SMTP(host=mx_server, port=25, timeout=5) as smtp:
                    (code, response) = smtp.getreply()
                    if code == 220:
                        return True
            except Exception as e:
                pass

        return False
