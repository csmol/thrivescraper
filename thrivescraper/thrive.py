"""Provide the primary functions."""

import argparse
import logging
import pprint
import sys

from .thrivescraper import ThriveScraper
import thrivescraper

logger = logging.getLogger("THRIVE")


def main(*args, db=None):
    # Create the argument parser and set the debug level ASAP
    parser = argparse.ArgumentParser(epilog="A subcommand is required.")

    parser.add_argument(
        "--version",
        action="version",
        version=f"THRIVE version {thrivescraper.__version__}",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        type=str.upper,
        choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="The level of informational output, defaults to '%(default)s'",
    )
    parser.add_argument(
        "--database",
        default="THRIVE.db",
        type=str,
        help="The THRIVE database, defaults to '%(default)s'",
    )

    # Parse the first options. If no args are passed in use sys.argv
    if len(args) == 0:
        args = [*sys.argv[1:]]
    else:
        args = [*args]

    if "-h" not in args and "--help" not in args:
        options, _ = parser.parse_known_args(args)
        kwargs = vars(options)

        # Set up the logging
        level = kwargs.pop("log_level", "WARNING")
        logging.basicConfig(level=level)

    # Now set up the rest of the parser
    subparser = parser.add_subparsers()

    ThriveScraper.setup_parser(subparser)

    # Parse the command-line arguments and call the requested function or the GUI
    logger.debug(f"{args=}")
    options = parser.parse_args(args)

    logger.debug(pprint.pformat(vars(options)))

    if "func" in options:
        try:
            result = options.func(options, db=db)
        except AttributeError as e:
            logger.debug(e)
            print(f"Missing arguments to THRIVE {' '.join(args)}")

            # Append help so help will be printed
            args.append("--help")
            # re-run
            main()
        else:
            if result is None:
                return 0
            else:
                return result
    else:
        # Append help so help will be printed
        print(f"Missing the subcommand for THRIVE {' '.join(args)}")
        args.append("--help")
        # re-run
        main(*args)
