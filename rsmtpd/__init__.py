"""
Main execution entry point: starts RSMTPD
"""

import sys

from argparse import ArgumentParser
from rsmtpd.core.logger_factory import LoggerFactory
from rsmtpd.core.server import Server
from rsmtpd.core.config_loader import ConfigLoader


def main(argv):
    """
    Starts RSMTPD. The start-up process entails:

      - Set up and parse command line arguments
      - Initialize the configuration reader
      - Start the server by running the rsmtpd.core.server class
    """

    # Set up the command line arguments and parse them
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-c", "--config-path", default=None,
                            help="Path to config file directory; if not specified, RSMTPD will look in ~/.rsmtpd,"
                                 "/etc/rsmtpd and $PWD/config in that order. RSMTPD config file must be named "
                                 "rsmtpd.conf.")
    arg_parser.add_argument("-a", "--address", default=None, help="Address to listen on (default: 127.0.0.1)")
    arg_parser.add_argument("-p", "--port", default=None, help="Port to listen on (default: 8025)")
    arg_parser.add_argument("-u", "--user", default="nobody",
                            help="User to run as when started as root (required to bind port 25; default: nobody)")
    arg_parser.add_argument("-b", "--background", action="store_true",
                            help="Run in the background (default: run in the foreground)")
    arg_parser.add_argument("-l", "--log-path", default=None,
                            help="Path to log files; if not specified, logs will be printed to stdout")
    arg_parser.add_argument("--log-level", default="warning",
                            help="Logging level; options are: error, warning, info, debug")
    args, other_args = arg_parser.parse_known_args(argv)

    # Start the logger
    # TODO: Allow setting the log level in the rsmtpd config file
    logger_factory = LoggerFactory(args.log_path, args.log_level)

    # Get the config loader
    config_loader = ConfigLoader(logger_factory, args.config_path)

    # Start the server
    server = Server(config_loader, logger_factory)
    server.run(args.address, args.port, args.user, args.background)


if __name__ == "__main__":
    main(sys.argv)
