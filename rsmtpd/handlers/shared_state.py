from uuid import uuid4


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

    # The IP address for the client
    remote_ip: str = None

    # The port number for the client
    remote_port: int = None

    # Whether TLS support is enabled and configured
    tls_available: bool = False

    # Whether TLS has been enabled in the session
    tls_enabled: bool = False

    # Whether the client is ESMTP capable (set by HELO or EHLO commands)
    esmtp_capable: bool = None

    # An internal class to represent the current command
    class CurrentCommand(object):
        # Whether the socket input buffer is empty; if false, it means the client is not waiting for responses before
        # sending data (violates RFC 5321 Section 4.3.1)
        buffer_is_empty = True

        # The last response received by the command handler for this command; helps command handlers merge responses
        response = None

    # An object with the current command information
    current_command: CurrentCommand = None

    def __init__(self, remote_address, tls_available=False):
        self.transaction_id = uuid4().hex
        self.tls_available = tls_available
        self.remote_ip = remote_address[0]
        self.remote_port = remote_address[1]
        self.current_command = self.CurrentCommand()
