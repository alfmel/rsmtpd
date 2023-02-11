from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState, ClientName
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.validators.domain import dns


class HelloHandler(BaseCommand):
    """
    The built-in command handler for the SMTP HELO and EHLO commands.
    """

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        shared_state.esmtp_capable = command.upper() == "EHLO"

        extensions = {
            "SIZE {}".format(shared_state.max_message_size),
            "8BITMIME",
            "SMTPUTF8"
        }

        if shared_state.client.tls_available and not shared_state.client.tls_enabled:
            extensions.add("STARTTLS")

        if "advertise_pipelining_extension" in self._config and self._config["advertise_pipelining_extension"]:
            extensions.add("PIPELINING")

        client_name = ClientName()
        client_name.name = argument.strip()
        if client_name.name and client_name.name.__contains__("."):
            client_name.forward_dns_ip = dns.by_name(client_name.name, shared_state.client.ip)
            client_name.is_valid_fqdn = bool(client_name.forward_dns_ip)
        else:
            client_name.is_valid_fqdn = False

        client_name.reverse_dns_name = dns.by_ip(shared_state.client.ip, client_name.name)

        shared_state.client_name = client_name
        shared_state.client.advertised_name = client_name.name  # TODO: Should we keep two versions of this?

        if "message" in self._config:
            message = self._config["message"]
        else:
            message = "Hello <client.advertised_name> (<client.ip> port <client.port>)"

        extended_message = [message]
        extended_message.extend(extensions)

        return SmtpResponse250(message, extended_message)
