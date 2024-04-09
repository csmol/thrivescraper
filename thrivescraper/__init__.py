"""A web scraper for the THRIVE project"""

# Add imports here
from .github import scrape_topic, use_api  # noqa: F401
from .thrivescraper import run  # noqa: F401

from ._version import __version__  # noqa: F401
