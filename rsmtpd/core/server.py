import socket
import threading

from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.core.logger_factory import LoggerFactory
from rsmtpd.core.tls import TLS
from rsmtpd.core.worker import Worker


class Server(object):
    __config_loader = None
    __logger_factory = None
    __logger = None
    __default_config = {
        "address": "127.0.0.1",
        "port": 8025,
        "user": "nobody",
        "background": False,
        "server_name": "mail.example.com",
        "tls": {
            "enabled": False,
            "certificates": []
        }
    }

    _config = None

    def __init__(self, config_loader: ConfigLoader, logger_factory: LoggerFactory):
        self.__config_loader = config_loader
        self.__logger_factory = logger_factory
        self.__logger = logger_factory.get_module_logger(self)
        self._tls = None

    def run(self, address=None, port=None, user=None, background=False):
        # Load the configuration
        self._load_config(address, port, user, background)

        # Initialize TLS
        self._tls = TLS(self._config["tls"]["enabled"], self._config["tls"]["certificates"], self.__logger_factory)
        self._tls.load_certificates_and_keys()

        # Open the socket
        self.__logger.debug("Attempting to listen on address %s and port %s",
                            self._config["address"], self._config["port"])
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self._config["address"], self._config["port"]))
        server.listen(1)
        self.__logger.info("RSMTPD server listening on %s:%s", self._config["address"], self._config["port"])

        # TODO: go to background if requested

        # TODO: shed privileges if root

        # Handle responses
        while True:
            (connection, address) = server.accept()
            thread = threading.Thread(target=self._handle_incoming_client, args=[connection, address], daemon=True)
            thread.start()

    def _handle_incoming_client(self, connection, remote_addr):
        # Load the worker and hand it the connection
        self.__logger.info("Received client connection from IP %s and port %s", remote_addr[0], remote_addr[1])
        self.__logger.debug("Starting server worker for incoming connection")
        worker = Worker(self._config["server_name"], self.__config_loader, self.__logger_factory)
        self.__logger.debug("Server worker started; transferring control to worker")
        worker.handle_client(connection, remote_addr, self._tls)

        # Close the connection
        self.__logger.info("Closing connection from IP %s and port %s", remote_addr[0], remote_addr[1])
        connection.close()

    def _load_config(self, address, port, user, background):
        # Load the configuration
        self._config = self.__config_loader.load_by_name("rsmtpd", "", self.__default_config)

        # Override settings from the command line
        if address is not None:
            self._config["address"] = address

        if port is not None:
            self._config["port"] = port

        if user is not None:
            self._config["user"] = user

        if background is not None:
            self._config["background"] = background
