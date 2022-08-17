import os.path
import unittest
from logging import Logger

from rsmtpd.core.validation import EmailAddressParseResult
from rsmtpd.handlers.data_file import DataToFileDataHandler
from rsmtpd.handlers.shared_state import SharedState
from tests.mocks import MockConfigLoader, StubLoggerFactory


class TestDataToFileDataHandler(unittest.TestCase):
    _mock_logger: Logger
    _mock_config_loader: MockConfigLoader

    def setUp(self):
        self._mock_logger = StubLoggerFactory().get_module_logger(None)
        self._mock_config_loader = MockConfigLoader(StubLoggerFactory())

    def test_handler_methods(self):
        handler = DataToFileDataHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.mail_from = EmailAddressParseResult()

        handler.handle_data(b"This is line 1\r\n", shared_state)
        handler.handle_data(b"This is line 2\r\n", shared_state)
        response = handler.handle_data_end(shared_state)

        self.assertEqual(response.get_code(), 250)
        self.assertIsNotNone(shared_state.data_filename)
        self.assertTrue(os.path.exists(shared_state.data_filename))

        with open(shared_state.data_filename) as data_file:
            data_output = data_file.read()

            self.assertTrue("line 1" in data_output)
            self.assertTrue("line 2" in data_output)

        os.unlink(shared_state.data_filename)

    def test_data_too_large(self):
        handler = DataToFileDataHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.mail_from = EmailAddressParseResult()
        shared_state.max_message_size = 0

        handler.handle_data(b"This should fail\r\n", shared_state)
        filename = shared_state.data_filename
        response = handler.handle_data_end(shared_state)

        self.assertEqual(response.get_code(), 552)
        self.assertIsNone(shared_state.data_filename)
        self.assertFalse(os.path.exists(filename))

    def test_mail_write_error(self):
        self._mock_config_loader.set_mock_config({"mail_spool_dir": "/rsmtpd/non-existent/path/to/force/failure"})
        handler = DataToFileDataHandler(self._mock_logger, self._mock_config_loader)
        shared_state = SharedState(("127.0.0.1", 12345))
        shared_state.mail_from = EmailAddressParseResult()

        handler.handle_data(b"Some mail data", shared_state)
        response = handler.handle_data_end(shared_state)

        self.assertEqual(response.get_code(), 451)


if __name__ == '__main__':
    unittest.main()
