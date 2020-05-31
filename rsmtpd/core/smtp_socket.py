from select import select
from socket import socket

from rsmtpd.exceptions import RemoteConnectionClosedException, LineLengthExceededException


class SMTPSocket(object):
    """
    Wrapper to a socket.socket object to facilitate SMTP send/receive operations
    """
    def __init__(self, connection: socket, read_size: int = 4096):
        self.__socket = connection
        self.__read_size = read_size
        self.__buffer = b""
        self.__has_been_read = False

    def buffer_is_empty(self):
        if self.__has_been_read:
            return len(self.__buffer) == 0
        else:
            r, w, e = select([self.__socket], [], [], 0.1)
            if len(r) > 0:
                return False
            return True

    def read(self) -> bytes:
        if len(self.__buffer):
            data = self.__buffer
            self.__clear_buffer()
        else:
            bytes_read = self.__socket.recv(self.__read_size)
            if len(bytes_read) == 0:
                raise RemoteConnectionClosedException("Client connection closed")
            self.__has_been_read = True
            data = bytes_read
        return data

    def read_line(self, limit=32768) -> bytearray:
        """
        Reads the buffer one line at a time. Returned data will contain LF.
        """
        while b"\n" not in self.__buffer:
            self.__buffer += self.read()
            if len(self.__buffer) > limit:
                raise LineLengthExceededException("The line received has exceeded the {}-byte limit".format(limit))

        line_length = self.__buffer.index(b"\n") + 1  # include LF in response
        line = self.__buffer[0:line_length]
        self.__buffer = self.__buffer[line_length:]

        return line

    def write(self, data: bytes) -> None:
        try:
            self.__socket.send(data)
        except Exception as e:
            raise RemoteConnectionClosedException("Client connection closed")

    def __clear_buffer(self) -> None:
        self.__buffer = b""
