from typing import Set, Union

from rsmtpd.core.validation import EmailAddressParseResult, EmailAddressVerificationResult
from uuid import uuid4


class Client(object):
    """
    Remote client connection information (static)
    """
    # The IP address for the client
    ip: str = None

    # The port number for the client
    port: int = None

    # Whether TLS support is enabled and configured
    tls_available: bool = False

    # Whether TLS has been enabled in the session
    tls_enabled: bool = False

    # The name given by the client during HELO/EHLO
    advertised_name: str = None

    def __init__(self, remote_address: (str, int), tls_available=False):
        self.ip = remote_address[0]
        self.port = remote_address[1]
        self.tls_available = tls_available
        self.advertised_name = "[{}:{}]".format(self.ip, self.port)


class CurrentCommand(object):
    """
    An object with the current command and connection buffer state
    """
    # Whether the socket input buffer is empty; if false, it means the client is not waiting for responses before
    # sending data (violates RFC 5321 Section 4.3.1 if PIPELINE is disabled)
    buffer_is_empty = True

    # The last response received by the command handler for this command; helps command handlers merge responses
    response = None


class ClientName(object):
    """
    An object for storing client greeting information
    """
    # The client name given by the client in HELO/EHLO command
    name: str = None

    # Whether the client name is a resolvable FQDN
    is_valid_fqdn: bool = None

    # The IP address associated with the given client name (None if not FQDN)
    forward_dns_ip: str = None

    # The reverse IP name (None if no reverse IP found)
    reverse_dns_name: str = None


class SharedState(object):
    """
    A shared state object that is passed to all commands.

    Properties at the top level are considered standard and anyone can access them. Handlers that wish to save their own
    state should use a top-level property with the name of the class of the handler (Logger, for example), using
    fully-qualified names if necessary.

    Because the shared state is available to all handlers, please be very careful when writing values to avoid
    clobbering them. Whenever possible, read any property you want, but only write to your handler's property.
    """

    # A unique transaction ID given to every session
    transaction_id: str = None

    # Remote client connection information
    client: Client = None

    # Remote client information gathered from HELO/EHLO command
    client_name: Union[ClientName, None] = None

    # Maximum message size in bytes (returned by EHLO response and enforced by DATA handler)
    max_message_size = 8388608

    # Whether the client is ESMTP capable (set by HELO or EHLO command handler)
    esmtp_capable: bool = False

    # Whether the last received command ended with proper CRLF
    last_command_has_standard_line_ending: Union[bool, None] = None

    # The parsed response from MAIL FROM command (None if command has not been executed)
    mail_from: Union[EmailAddressParseResult, None] = None

    # The set of recipients
    recipients: Set[EmailAddressVerificationResult] = set()

    # The full path and filename where the mail DATA is stored
    data_filename: Union[str, None] = None

    # An object with the current command information
    current_command: CurrentCommand = None

    def __init__(self, remote_address, tls_available=False):
        self.transaction_id = uuid4().hex
        self.client = Client(remote_address, tls_available)
        self.client_name = None
        self.esmtp_capable = False
        self.last_command_has_standard_line_ending = None
        self.mail_from = None
        self.recipients = set()
        self.data_filename = None
        self.current_command = CurrentCommand()
