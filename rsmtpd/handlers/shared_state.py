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
    transaction_id = None
    remote_ip = None
    remote_port = None

    def __init__(self, remote_address):
        self.transaction_id = uuid4().hex
        self.remote_ip = remote_address[0]
        self.remote_port = remote_address[1]
