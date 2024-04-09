"""Provide the primary functions."""

import csv
import json  # noqa: F401
from pathlib import Path  # noqa: F401
import pprint  # noqa: F401

import thrivescraper


def run():
    # result = thrivescraper.scrape_topic("computational-materials-science")

    topics = (
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
    # topics = ("computational-materials-engineering",)

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
