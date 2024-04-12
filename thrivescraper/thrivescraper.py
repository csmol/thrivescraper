"""Provide the primary functions."""

import logging
import pprint

from .github import GitHub
from .thrive_db import ThriveDB
from .util import iso_to_timestamp

logger = logging.getLogger(__name__)


class ThriveScraper(object):
    """Class for scraping GitHub and other sites for data."""

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

    def __init__(self, options, logger=logger, gh=None, db=None):
        self.logger = logger
        self._db = db
        self._gh = gh
        self._options = vars(options)

    @classmethod
    def mine_topics_helper(cls, options, gh=None, db=None):
        """Thin wrapper for mining topics."""
        scraper = cls(options, gh=gh, db=db)
        scraper.mine_topics()
        return 0

    @classmethod
    def setup_parser(cls, subparser):
        """Setup the parser for getting the repos in topics."""
        parser = subparser.add_parser("mine-topics")
        parser.set_defaults(func=cls.mine_topics_helper)
        parser.add_argument(
            "topics",
            nargs="*",
            default=cls.default_topics,
            help="The topics for gathering repos.",
        )
        parser.add_argument(
            "--repos-file",
            help="The csv file for the repos info if not None.",
        )
        parser.add_argument(
            "--topics-file",
            help="The csv file for the topics if not None.",
        )

    @property
    def db(self):
        """The THRIVE database"""
        if self._db is None:
            self._db = ThriveDB(**self.options)

        return self._db

    @property
    def gh(self):
        """Our GitHub handler"""
        if self._gh is None:
            self._gh = GitHub()

        return self._gh

    @property
    def options(self):
        """The options from the command line."""
        return self._options

    def mine_topics(self):
        topics = self.options["topics"]

        table = self.db["repos"]
        category_id = self.db.get_category_id("none")
        total_added = 0
        n_total = 0
        for topic in topics:
            n_added = 0
            repo_data = self.gh.search_repositories(f"topic:{topic}")
            n_total += len(repo_data)
            for item in repo_data.values():
                # remove unwanted keys
                del item["owner"]
                keys = [*item.keys()]
                for key in keys:
                    if "url" in key:
                        del item[key]

                self.logger.debug(pprint.pformat(item))

                # Insert into the database as needed
                full_name = item["full_name"]

                if not self.db.repo_exists(full_name):
                    n_added += 1

                    if item["license"] is None:
                        license = None
                    else:
                        license = item["license"]["name"]

                    organization = item["organization"]
                    if not self.db.organization_exists(organization):
                        self.db["organizations"].append(name=organization)
                    organization_id = self.db.get_organization_id(organization)

                    table.append(
                        active=0,
                        category=category_id,
                        full_name=full_name,
                        organization=organization_id,
                        name=item["name"],
                        created_at=iso_to_timestamp(item["created_at"]),
                        default_branch=item["default_branch"],
                        description=item["description"],
                        homepage=item["homepage"],
                        language=item["language"],
                        license=license,
                        node_id=item["node_id"],
                        pushed_at=iso_to_timestamp(item["pushed_at"]),
                        updated_at=iso_to_timestamp(item["updated_at"]),
                    )

                # And insert/update the topics
                repo_id = self.db.get_repo_id(full_name)
                previous = self.db.get_repo_topics(repo_id)
                for _topic in item["topics"]:
                    if _topic not in previous:
                        if self.db.topic_exists(_topic):
                            topic_id = self.db.get_topic_id(_topic)
                        else:
                            topic_id = self.db["topics"].append(name=_topic)
                        self.db["repos_topics"].append(repo=repo_id, topic=topic_id)

            print(
                f"Found {n_added} new repos out of {len(repo_data)} for topic {topic}."
            )
            total_added += n_added

        print(f"Found {total_added} new repos out of the total of {n_total}.")

        if False:
            print()
            print("Repos")
            print(table)
            print()
            print("Topics")
            print(self.db["topics"])
