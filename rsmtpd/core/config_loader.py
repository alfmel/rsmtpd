import os
from typing import Dict

from yaml import load, SafeLoader, YAMLError

from rsmtpd.core.logger_factory import LoggerFactory


class ConfigLoader(object):
    """
    The RSMTPD config object allows modules to load their configuration files quickly and easily. The object takes an
    optional path where configuration files will be stored. If no path is specified, the object will look in the the
    following directories. The first directory to exist will become the configuration directory for the entire execution
    of the daemon. The paths are:

      ~/.rsmtpd
      /etc/rsmtpd
      $PWD/config (mostly for development)

    TODO: Merge config files with default to ensure we have initial values
    """

    __path = None
    __logger = None

    def __init__(self, logger: LoggerFactory, path: str = None):
        """
        Checks to see where config files will be coming from. If no suitable directory is found, default values will
        always be used.

        :param logger: Logger instance
        :param path: Optional path to configuration files
        """

        self.__logger = logger.get_module_logger(self)

        # Check if the given path exists
        if path is not None:
            if os.path.isdir(path):
                self.__path = path
            else:
                self.__logger.error("Specified config directory %s does not exist", path)

        if self.__path is None:
            if os.path.isdir("~/.rsmtpd"):
                self.__path = "~/.rsmtpd"
            elif os.path.isdir("/etc/rsmtpd"):
                self.__path = "/etc/rsmtpd"
            elif os.path.isdir("config"):
                self.__path = "config"

        if self.__path is None:
            self.__logger.critical("No valid configuration directory found. Valid directories are ~/.rsmtpd, "
                                   "/etc/rsmtpd, $PWD/config or a path specified in the command line with "
                                   "--config-path option. Built-in defaults will be used.")
        else:
            self.__logger.info("Config path: %s", self.__path)

    def load(self, class_ref: object, suffix: str = "", default: Dict = None) -> Dict:
        """
        Load a YAML configuration for a given object based on the module or class name, with an optional suffix.

        If the class/object points to a class named ExtHello in the module rsmtpd.handlers.ehlo, the loader will look
        for the following files in the configuration directory in this order:

          rsmtpd.handlers.hello.yaml
          hello.yaml
          ExtHello.yaml

        If a suffix of "alt" is passed with the same class reference, the loader will look for the following files in
        this order:

          rsmtpd.handlers.ehlo_alt.yaml
          ehlo_alt.yaml
          ExtHello_alt.yaml

        As a rule of thumb, standard rsmtpd config files should use the last part of the module name (hello.yaml) while
        external modules should use the fully qualified module name (rsmtpd.john_doe.handlers.hello.yaml) for their
        configuration to avoid conflicts.

        :param class_ref: The class or object to load the config for
        :param suffix:    Optional suffix to load alternate configuration
        :param default:   Default configuration to return if no config file is found

        :return: Dictionary with configuration
        """
        if default is None:
            default = {}

        if self.__path is None:
            return default

        # Try loading by the fully qualified class name first
        config_file = self._get_path_name(type(class_ref).__module__, suffix)
        if os.path.isfile(config_file):
            with open(config_file) as stream:
                try:
                    config = load(stream, Loader=SafeLoader)
                    self.__logger.info("Loaded configuration from \"%s\"", config_file)
                    return config
                except YAMLError:
                    self.__logger.error("Could not parse YAML config file \"%s\"; using default configuration",
                                        config_file)
                    return default
        self.__logger.debug("Configuration file \"%s\" not found", config_file)

        # Try loading by the last part of the module
        config_file = self._get_path_name(type(class_ref).__module__.split(".")[-1], suffix)
        if os.path.isfile(config_file):
            with open(config_file) as stream:
                try:
                    config = load(stream, Loader=SafeLoader)
                    self.__logger.info("Loaded configuration from \"%s\"", config_file)
                    return config
                except YAMLError:
                    self.__logger.error("Could not parse YAML config file \"%s\"; using default configuration",
                                        config_file)
                    return default
        self.__logger.debug("Configuration file \"%s\" not found", config_file)

        # Try loading by the class name only
        config_file = self._get_path_name(type(class_ref).__name__, suffix)
        if os.path.isfile(config_file):
            with open(config_file) as stream:
                try:
                    config = load(stream, Loader=SafeLoader)
                    self.__logger.info("Loaded configuration from \"%s\"", config_file)
                    return config
                except YAMLError:
                    self.__logger.error("Could not parse YAML config file \"%2\"; using default configuration",
                                        config_file)
                    return default

        # No config for this class; use default
        self.__logger.debug("Configuration file \"%s\" not found; using default configuration", config_file)
        return default

    def load_by_name(self, name: str, suffix: str = "", default: Dict = None):
        """
        Load a YAML configuration with the given name with an optional suffix.

        If the name of "my_config" is passed with no suffix, the loader will look for "my_config.yaml" in the
        configuration directory. If a suffix of "alt" is passed, the loader will look for "my_config_alt.yaml".

        :param name:    Config file name
        :param suffix:  Optional suffix to load alternate configuration
        :param default: Default configuration to return if no config file is found

        :return: Dictionary with configuration
        """
        if default is None:
            default = {}

        if self.__path is None:
            return default

        config_file = self._get_path_name(name, suffix)
        if os.path.isfile(config_file):
            with open(config_file) as stream:
                try:
                    config = load(stream, Loader=SafeLoader)
                    self.__logger.info("Loaded configuration from \"%s\"", config_file)
                    return config
                except YAMLError:
                    self.__logger.error("Could not parse YAML config file \"%s\"; using default configuration",
                                        config_file)
                    return default

                    # No config for this class; use default
        self.__logger.debug("Configuration file \"%s\" not found; using default configuration", config_file)
        return default

    def _get_path_name(self, name: str, suffix: str):
        """
        Adds the suffix (if one is passed) and the .yaml extension to the given name.
        """
        if len(suffix) > 0:
            return os.path.join(self.__path, name + "_" + suffix + ".yaml")
        else:
            return os.path.join(self.__path, name + ".yaml")
