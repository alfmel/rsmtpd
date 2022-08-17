import unittest
from logging import Logger
from rsmtpd.handlers.hello import HelloHandler
from rsmtpd.handlers.shared_state import SharedState, ClientName
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestHelloHandler(unittest.TestCase):
    """
    Unit test for the Hello command handler
    """

    _mock_logger: Logger

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)

    def test_no_config(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        handler = HelloHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("EHLO", "example.com", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertNotEqual(response.get_message(), "")
        self.assertNotEqual(response.get_multi_line_message()[0], "")
        self.assertFalse("PIPELINING" in response.get_multi_line_message())
        self.assertTrue("SIZE {}".format(shared_state.max_message_size) in response.get_multi_line_message())
        self.assertTrue(shared_state.esmtp_capable)
        self.assertEqual(shared_state.client.advertised_name, "example.com")
        self.assertIsInstance(shared_state.client_name, ClientName)
        self.assertEqual(shared_state.client_name.name, "example.com")
        self.assertTrue(shared_state.client_name.is_valid_fqdn)
        self.assertIsNotNone(shared_state.client_name.forward_dns_ip)
        self.assertIsNotNone(shared_state.client_name.reverse_dns_name)

    def test_custom_message(self):
        message = "Custom message"
        mock_config_loader = MockConfigLoader(StubLoggerFactory(), {"message": message})
        shared_state = SharedState(("127.0.0.1", 12345))
        handler = HelloHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("EHLO", "example.com", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertEqual(response.get_message(), message)
        self.assertEqual(response.get_multi_line_message()[0], message)

    def test_advertise_pipelining(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory(), {"advertise_pipelining_extension": True})
        shared_state = SharedState(("127.0.0.1", 12345))
        handler = HelloHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("EHLO", "example.com", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertTrue("PIPELINING" in response.get_multi_line_message())

    def test_helo(self):
        message = "Custom message"
        mock_config_loader = MockConfigLoader(StubLoggerFactory(), {"message": message})
        shared_state = SharedState(("127.0.0.1", 12345))
        handler = HelloHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("HELO", "example.com", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertEqual(response.get_message(), message)
        self.assertFalse(shared_state.esmtp_capable)
        self.assertEqual(shared_state.client.advertised_name, "example.com")
        self.assertIsInstance(shared_state.client_name, ClientName)
        self.assertEqual(shared_state.client_name.name, "example.com")

    def test_bad_name(self):
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        shared_state = SharedState(("127.0.0.1", 12345))
        handler = HelloHandler(self._mock_logger, mock_config_loader)

        response = handler.handle("EHLO", "bad-name", shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertTrue(shared_state.esmtp_capable)
        self.assertEqual(shared_state.client.advertised_name, "bad-name")
        self.assertIsInstance(shared_state.client_name, ClientName)
        self.assertEqual(shared_state.client_name.name, "bad-name")
        self.assertFalse(shared_state.client_name.is_valid_fqdn)
        self.assertIsNone(shared_state.client_name.forward_dns_ip)


if __name__ == '__main__':
    unittest.main()
