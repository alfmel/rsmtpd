import unittest

from rsmtpd.handlers.shared_state import Client, SharedState, CurrentCommand


class TestClient(unittest.TestCase):
    def test_constructor(self):
        test_ip = "1.2.3.4"
        test_port = 2345
        test_tls_available = True

        client = Client((test_ip, test_port), test_tls_available)

        self.assertEqual(client.ip, test_ip)
        self.assertEqual(client.port, test_port)
        self.assertEqual(client.tls_available, test_tls_available)
        self.assertEqual(client.tls_enabled, False)
        self.assertEqual(client.advertised_name, "[{}:{}]".format(test_ip, test_port))


class TestSharedState(unittest.TestCase):
    def test_constructor(self):
        test_ip = "4.3.2.1"
        test_port = 5432
        test_tls_available = False

        shared_state = SharedState((test_ip, test_port), test_tls_available)

        self.assertIsNotNone(shared_state.transaction_id)
        self.assertNotEqual(shared_state.transaction_id, "")
        self.assertIsInstance(shared_state.client, Client)
        self.assertEqual(shared_state.client.ip, test_ip)
        self.assertEqual(shared_state.client.port, test_port)
        self.assertEqual(shared_state.client.tls_enabled, test_tls_available)
        self.assertIsNone(shared_state.client_name)
        self.assertEqual(shared_state.esmtp_capable, test_tls_available)
        self.assertIsNone(shared_state.last_command_has_standard_line_ending)
        self.assertIsNone(shared_state.mail_from)
        self.assertIsInstance(shared_state.recipients, set)
        self.assertEqual(len(shared_state.recipients), 0)
        self.assertIsNone(shared_state.data_filename)
        self.assertIsInstance(shared_state.current_command, CurrentCommand)


if __name__ == '__main__':
    unittest.main()
