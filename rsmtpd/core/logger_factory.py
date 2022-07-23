import logging


class LoggerFactory(object):
    """
    The RSMTPD Logger class handles logging operations for the entire daemon. It stores the path to the logging
    directory passed during instantiation. Other parts of the code will inject loggers into the plugins as necessary by
    calling get_module_logger() with the name of the class
    """

    __path = None
    __logger = None
    __log_level = None

    def __init__(self, path: str = None, level: str = "info"):
        level_lower = str.lower(level or "info")
        if level_lower == "critical":
            self.__log_level = logging.CRITICAL
        elif level_lower == "error":
            self.__log_level = logging.ERROR
        elif level_lower == "warning":
            self.__log_level = logging.WARNING
        elif level_lower == "info":
            self.__log_level = logging.INFO
        elif level_lower == "debug":
            self.__log_level = logging.DEBUG
        else:
            self.__log_level = logging.INFO

        if path is not None:
            self.__path = path

        # TODO: Set up logging to files; for right now, all logging will be to stdout
        logging.basicConfig(level=self.__log_level, format="%(asctime)s %(levelname)s (%(name)s): %(message)s")
        self.__logger = logging.Logger("rsmtpd", self.__log_level)

    def get_module_logger(self, module: object) -> logging.Logger:
        logger = self.__logger.getChild(type(module).__name__)
        # logger.setLevel(self.__log_level)
        return logger

    def get_child_logger(self, name: str) -> logging.Logger:
        return self.__logger.getChild(name)
