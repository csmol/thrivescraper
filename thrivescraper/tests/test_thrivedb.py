"""Unit and regression test for the ThriveDB."""

# Import package, test suite, and other packages as needed
import pytest  # noqa: F401

from thrivescraper import ThriveDB


def test_create_db():
    """Test that we can make a database"""
    db = ThriveDB(database="file:thrive_create_db?mode=memory&cache=shared")
    assert type(db) is ThriveDB
