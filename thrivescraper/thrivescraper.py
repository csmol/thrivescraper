"""Provide the primary functions."""

import argparse
import csv
import json  # noqa: F401
import logging
from pathlib import Path  # noqa: F401
import pprint  # noqa: F401
import sys

import thrivescraper

logger = logging.getLogger("THRIVE")
options = {}

default_topics = (
    "materials",
    "materials-science",
    "materials-informatics",
    "computational-materials-science",
    "materials-design",
    "materials-discovery",
    "materials-genome",
    "materials-platform",
    "computational-materials",
    "materials-modeling",
    "computational-materials-engineering",
    "materials-simulation",
    "optimade",
    "ab-initio",
    "quantum-chemistry",
    "computational-chemistry",
)


def run():
    # Create the argument parser and set the debug level ASAP
    global options

    parser = argparse.ArgumentParser(
        epilog="If no positional argument is given, the GUI will appear."
    )

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
        help=("The level of informational output, defaults to " "'%(default)s'"),
    )

    # Parse the first options
    if "-h" not in sys.argv and "--help" not in sys.argv:
        options, _ = parser.parse_known_args()
        kwargs = vars(options)

        # Set up the logging
        level = kwargs.pop("log_level", "WARNING")
        logging.basicConfig(level=level)

    # Now set up the rest of the parser
    subparser = parser.add_subparsers()

    setup_topic_handler(subparser)

    # Parse the command-line arguments and call the requested function or the GUI
    options = parser.parse_args()

    if "func" in options:
        try:
            sys.exit(options.func())
        except AttributeError:
            print(f"Missing arguments to THRIVE {' '.join(sys.argv[1:])}")
            # Append help so help will be printed
            sys.argv.append("--help")
            # re-run
            run()


def setup_topic_handler(subparser):
    """Setup the parser for getting the repos in topics."""
    parser = subparser.add_parser("mine-topics")
    parser.set_defaults(func=topic_handler)
    parser.add_argument(
        "topics",
        nargs="*",
        default=default_topics,
        help="The topics for gathering repos.",
    )


def topic_handler():
    global options

    topics = options.topics

    repos = {}
    topic_set = set()
    for topic in topics:
        result = thrivescraper.use_api(topic)

        for item in result.values():
            topic_set.update(item["topics"])
            item["topics"] = " ".join(item["topics"])
        len1 = len(repos)
        len2 = len(result)
        repos.update(**result)
        len3 = len(repos)
        print(f"{topic:40s} {len2} repos of which {len3-len1} are new.")

    to_csv(repos, "test.csv")

    all_topics = sorted(topic_set)
    with open("topics.csv", "w", newline="") as fd:
        writer = csv.writer(fd)
        writer.writerow(["Topic"])
        for top in all_topics:
            writer.writerow([top])
    print(f"{len(all_topics)} topics were written to topics.csv")


def to_csv(data, path):
    """Write the dictionary as CSV to the path"""

    fieldnames = [key for key in next(iter(data.values())).keys()]

    row = 0
    with open(path, "w", newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames)
        writer.writeheader()
        for item in data.values():
            row += 1
            item["row"] = row
            writer.writerow(item)
    print(f"Wrote {row} rows to CSV file {path}")


if __name__ == "__main__":
    # Do something if this file is invoked on its own
    run()
