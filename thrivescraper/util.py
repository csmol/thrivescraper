"""Utility routines for THRIVE."""

import csv
from datetime import datetime, timezone


def dict_to_csv(data, path):
    """Write the dictionary as CSV to the path"""

    fieldnames = ["row"]
    fieldnames.extend([key for key in next(iter(data.values())).keys()])

    row = 0
    with open(path, "w", newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames)
        writer.writeheader()
        for item in data.values():
            row += 1
            item["row"] = row
            writer.writerow(item)
    return f"Wrote {row} rows to CSV file {path}"


def iso_to_timestamp(text):
    """Convert an ISO date/time string to an integer timestamp"""
    return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp())
