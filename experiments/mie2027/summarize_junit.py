#!/usr/bin/env python3
"""Create compact, machine-readable summaries from Maven Surefire XML."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from xml.etree import ElementTree


def numeric(value: str | None) -> float:
    return float(value or 0)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: summarize_junit.py SUREFIRE_DIRECTORY OUTPUT_DIRECTORY", file=sys.stderr)
        return 2

    report_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for report in sorted(report_dir.glob("TEST-*.xml")):
        root = ElementTree.parse(report).getroot()
        rows.append(
            {
                "suite": root.attrib.get("name", report.stem.removeprefix("TEST-")),
                "tests": int(root.attrib.get("tests", 0)),
                "failures": int(root.attrib.get("failures", 0)),
                "errors": int(root.attrib.get("errors", 0)),
                "skipped": int(root.attrib.get("skipped", 0)),
                "time_seconds": numeric(root.attrib.get("time")),
                "source": report.name,
            }
        )

    totals = {
        key: sum(row[key] for row in rows)
        for key in ("tests", "failures", "errors", "skipped", "time_seconds")
    }
    summary = {
        "evidence_level": "component",
        "suite_count": len(rows),
        "totals": totals,
        "suites": rows,
    }

    with (output_dir / "junit-summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")

    with (output_dir / "junit-summary.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["suite", "tests", "failures", "errors", "skipped", "time_seconds", "source"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    raw_dir = output_dir / "surefire-reports"
    raw_dir.mkdir(exist_ok=True)
    for report in sorted(report_dir.glob("TEST-*.xml")):
        (raw_dir / report.name).write_bytes(report.read_bytes())

    if not rows:
        print(f"No Surefire XML reports found in {report_dir}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

