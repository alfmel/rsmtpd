import unittest

from rsmtpd.core.tls import TLS
from tests.mocks import StubLoggerFactory


class TestTLS(unittest.TestCase):
    """
    Unit test for TLS manager
    """
    def setUp(self) -> None:
        self._stub_logger_factory = StubLoggerFactory()

    def test_load_certificates_and_keys(self):
        tls = TLS(True, self._get_test_certificates(), self._stub_logger_factory)
        tls.load_certificates_and_keys()
        # Loading should fail, and TLS should be disabled
        self.assertFalse(tls.enabled())

    def test_enabled(self):
        # Should honor enabled flag
        tls = TLS(False, self._get_test_certificates(), self._stub_logger_factory)
        self.assertFalse(tls.enabled())

        # Should stay enabled if enabled with certificates
        tls = TLS(True, self._get_test_certificates(), self._stub_logger_factory)
        self.assertTrue(tls.enabled())

        # Should disable if there are no certificates
        tls = TLS(True, [], self._stub_logger_factory)
        self.assertFalse(tls.enabled())

    def test_select_certificate(self):
        certs = self._get_test_certificates()
        tls = TLS(True, certs, self._stub_logger_factory)

        certificate = tls.select_certificate("mail.example.com")
        self.assertEqual(certificate, certs[0])

        certificate = tls.select_certificate("mail.example.net")
        self.assertEqual(certificate, certs[1])

        # Should fall back to first certificate if there is no match
        certificate = tls.select_certificate("smtp.example.org")
        self.assertEqual(certificate, certs[0])

    def test_select_certificate_single_certificate(self):
        cert = self._get_test_certificates()[1]
        tls = TLS(True, [cert], self._stub_logger_factory)

        certificate = tls.select_certificate("mail.example.net")
        self.assertEqual(certificate, cert)

    def _get_test_certificates(self):
        return [
            {
                "domain_match": "example.com",
                "server_name": "mail.example.com",
                "pem_file": "/path/to/com.pem",
                "key_file": "/path/to/com.key"
            },
            {
                "domain_match": "example.net",
                "server_name": "mail.example.net",
                "pem_file": "/path/to/net.pem",
                "key_file": "/path/to/net.key"
            }
        ]


if __name__ == '__main__':
    unittest.main()
