#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Fixtures for testing the 'thrivescraper' package."""
from pathlib import Path

import pytest

from thrivescraper import ThriveDB

path = Path(__file__).resolve().parent
data_path = path / "data"


def pytest_addoption(parser):
    parser.addoption(
        "--run-timing", action="store_true", default=False, help="run timing tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "timing: mark test as timing to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-timing"):
        # --run-timing given in cli: do not skip timing tests
        return
    skip_timing = pytest.mark.skip(reason="need --run-timing option to run")
    for item in items:
        if "timing" in item.keywords:
            item.add_marker(skip_timing)


@pytest.fixture()
def db():
    """Create a THRIVE db in memory."""
    db = ThriveDB(database="file:thrive_db?mode=memory&cache=shared")

    yield db

    db.close()
    try:
        del db
    except:  # noqa: E722
        print("Caught error deleting the database")
