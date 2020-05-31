import unittest

from rsmtpd.core.smtp_socket import SMTPSocket
from rsmtpd.exceptions import LineLengthExceededException
from tests.mocks import get_mock_socket


class TestSocketWrapper(unittest.TestCase):
    def test_read(self):
        test_data = b"abc123\r\nxyz789\r\n"
        mock_socket = get_mock_socket()
        mock_socket.recv.configure_mock(return_value=test_data)

        socket_wrapper = SMTPSocket(mock_socket)
        result = socket_wrapper.read()
        self.assertEqual(result, test_data)

    def test_read_line(self):
        mock_socket = get_mock_socket()
        mock_socket.recv.configure_mock(return_value=b"abc123\r\nxyz789\r\n")

        socket_wrapper = SMTPSocket(mock_socket)
        result = socket_wrapper.read_line()
        self.assertEqual(result, b"abc123\r\n")

        result = socket_wrapper.read_line()
        self.assertEqual(result, b"xyz789\r\n")

        mock_socket.recv.reset_mock()
        mock_socket.recv.configure_mock(return_value=b"abc123\nxyz789\r\n")

        result = socket_wrapper.read_line()
        self.assertEqual(result, b"abc123\n")

        result = socket_wrapper.read_line()
        self.assertEqual(result, b"xyz789\r\n")

    def test_read_after_read_line(self):
        mock_socket = get_mock_socket()
        mock_socket.recv.configure_mock(return_value=b"abc123\r\nxyz789\r\n")

        socket_wrapper = SMTPSocket(mock_socket)
        result = socket_wrapper.read_line()
        self.assertEqual(result, b"abc123\r\n")
        result = socket_wrapper.read()
        self.assertEqual(result, b"xyz789\r\n")

        result = socket_wrapper.read()
        self.assertEqual(result, b"abc123\r\nxyz789\r\n")

    def test_read_line_limit(self):
        mock_socket = get_mock_socket()
        mock_socket.recv.configure_mock(return_value=b"abcd1234")

        socket_wrapper = SMTPSocket(mock_socket)
        try:
            socket_wrapper.read_line()
        except LineLengthExceededException as e:
            pass
        except Exception as e:
            self.fail("Expected exception not raised")

    def test_buffer_is_empty(self):
        mock_socket = get_mock_socket()
        mock_socket.recv.configure_mock(return_value=b"abc123\r\nxyz789\r\n")
        socket_wrapper = SMTPSocket(mock_socket)

        socket_wrapper.read_line()
        self.assertFalse(socket_wrapper.buffer_is_empty())
        socket_wrapper.read_line()
        self.assertTrue(socket_wrapper.buffer_is_empty())

    def test_write(self):
        mock_socket = get_mock_socket()
        socket_wrapper = SMTPSocket(mock_socket)

        test_data = b"abc123\r\n"
        socket_wrapper.write(test_data)
        mock_socket.send.assert_called_with(test_data)


if __name__ == '__main__':
    unittest.main()
