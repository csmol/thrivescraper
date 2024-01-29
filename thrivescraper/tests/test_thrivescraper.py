"""
Unit and regression test for the thrivescraper package.
"""

# Import package, test suite, and other packages as needed
import sys

import pytest

import thrivescraper


def test_thrivescraper_imported():
    """Sample test, will always pass so long as import statement worked."""
    assert "thrivescraper" in sys.modules
