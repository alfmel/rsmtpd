from unittest import TestCase, main

from rsmtpd.core.worker import Worker
from tests.mocks import MockLogger, StubLoggerFactory, MockConfigLoader


class TestWorker(TestCase):
    __worker = None

    def setUp(self):
        stub_logger_factory = StubLoggerFactory()
        self.__worker = Worker("unit.test", MockConfigLoader(stub_logger_factory), stub_logger_factory)

    def testGetCommandWithArgument(self):
        self.assertTrue(True)


if __name__ == '__main__':
    main()
