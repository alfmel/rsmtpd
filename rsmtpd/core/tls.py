import ssl
from socket import socket
from ssl import SSLContext
from typing import Dict, List

from rsmtpd import LoggerFactory
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_454 import SmtpResponse454


class TLS(object):
    """
    Handles TLS certificate loading, selection via SNI and socket wrapping
    """
    def __init__(self, enabled: bool, certificates: List[Dict], logger_factory: LoggerFactory):
        self._enabled = enabled and len(certificates) > 0
        self._certificates = certificates
        self._logger = logger_factory.get_module_logger(self)
        self._server_name = ""

    def load_certificates_and_keys(self):
        loaded_certificates = []
        for certificate in self._certificates:
            try:
                self._load_file(certificate["pem_file"])
                # TODO: We must find a way to load the keys to memory so we can read them as root and shed privileges
                # certificate["key_file"] = self._load_file(certificate["key_file"])
                self._load_file(certificate["key_file"])
                loaded_certificates.append(certificate)
            except Exception as e:
                self._logger.warning("Certificate for {} disabled".format(certificate["server_name"]))

        if len(loaded_certificates):
            self._certificates = loaded_certificates
            self._logger.info("TLS initialized with {} certificate(s)".format(len(loaded_certificates)))
        else:
            self._enabled = False
            self._logger.warning("No valid certificates could be loaded; TLS disabled")

    def enabled(self) -> bool:
        return self._enabled

    def start(self, connection: socket) -> (socket, BaseResponse):
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.sni_callback = lambda conn, server_name, ssl_context: \
                self.select_certificate(conn, server_name, ssl_context)
            tls_connection = context.wrap_socket(connection, server_side=True)
            return tls_connection, None, self._server_name
        except Exception as e:
            self._logger.error("Unable to start TLS", e)
            return connection, SmtpResponse454()

    def select_certificate(self, connection: ssl.SSLSocket, server_name: str, context: SSLContext):
        certificate_count = len(self._certificates)
        if certificate_count > 1 and server_name:
            certificate = None
            for cert in self._certificates:
                if cert["domain_match"] in server_name:
                    certificate = cert
                    break
            if not certificate:
                certificate = self._certificates[0]
        elif certificate_count == 0:
            raise Exception("Cannot initiate TLS: no certificates")
        else:
            certificate = self._certificates[0]

        new_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        new_context.load_cert_chain(certificate["pem_file"], certificate["key_file"])
        connection.context = new_context
        self._server_name = certificate["server_name"]
        self._logger.info("Loaded certificate for {} based on server name \"{}\""
                          .format(certificate["server_name"], server_name))

    def _load_file(self, filename: str) -> str:
        try:
            with open(filename) as f:
                return f.read()
        except Exception as e:
            self._logger.warning("Unable to read {}: {}".format(filename, e))
            raise e
