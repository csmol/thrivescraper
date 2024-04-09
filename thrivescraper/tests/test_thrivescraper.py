"""
Unit and regression test for the thrivescraper package.
"""

# Import package, test suite, and other packages as needed
import sys

import pytest  # noqa: F401

import thrivescraper  # noqa: F401


def test_thrivescraper_imported():
    """Sample test, will always pass so long as import statement worked."""
    assert "thrivescraper" in sys.modules


def test_topic():
    """Simple test to find the repos in a topic.

    From time-to-time new repositories may be created with this topic, in which case
    the new repos need to be added to the list below.
    """
    correct = [
        "LiUSemWeb/Materials-Design-Ontology",
        "Materials-Consortia/OPTIMADE",
        "Materials-Consortia/OPTIMADE-Filter",
        "Materials-Consortia/optimade-gateway",
        "Materials-Consortia/optimade-python-tools",
        "Materials-Consortia/optimade-tutorial-exercises",
        "Materials-Consortia/providers-dashboard",
        "SINTEF/oteapi-optimade",
        "basf/metis-gui",
        "blokhin/materials-informatics-tutorial",
        "materialscloud-org/optimade-maker",
        "merkys/OPTIMADE-PropertyDefinitions",
        "ml-evs/necroptimade",
        "ml-evs/odbx.science",
        "mpds-io/optimade-mpds-nlp",
        "tachyontraveler/oqmd-optimade-tutorial",
        "tilde-lab/chemdoodle-optimade-app",
        "tilde-lab/cifplayer",
        "tilde-lab/jsmol-optimade-app",
        "tilde-lab/optimade-client",
        "tilde-lab/optimade.science",
    ]

    result = thrivescraper.use_api("optimade")

    keys = sorted(result.keys())

    if keys != correct:
        print(keys)

    assert keys == correct
