"""CTCAE v5.0 laboratory grading for two explicitly supported hematologic terms.

The rules are transcribed from NCI CTCAE v5.0 (2017), Investigations:
https://dctd.cancer.gov/research/ctep-trials/for-sites/adverse-events/ctcae-v5-8x11.pdf

Counts are cells per microliter (/uL). Not a general CTCAE grader or a
clinical decision support substitute. No treatment recommendation is made.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

# Lower bound for Grades 1, 2, and 3 (Grade 4 is below the final bound).
# Both adverse-event terms have no Grade 5 criterion in CTCAE v5.
TERMS = {
    "Neutrophil count decreased": (1500.0, 1000.0, 500.0),
    "Platelet count decreased": (75000.0, 50000.0, 25000.0),
}
SOURCE_URL = "https://dctd.cancer.gov/research/ctep-trials/for-sites/adverse-events/ctcae-v5-8x11.pdf"


def grade_lab_event(term: str, value: float, lln: float) -> dict:
    """Return the CTCAE v5 grade (1-4), or None if value is not below LLN.

    Grade boundaries use their documented inclusive lower bound.
    Only the two supported laboratory terms and counts per /uL are accepted.
    A laboratory-specific LLN is required to distinguish normal from Grade 1.
    """
    if term not in TERMS:
        raise ValueError(f"Unsupported CTCAE term: {term!r}. Choose one of: {', '.join(TERMS)}")
    try:
        measured, lower_limit = float(value), float(lln)
    except (TypeError, ValueError) as exc:
        raise ValueError("value and lln must be finite numbers") from exc
    if not (math.isfinite(measured) and math.isfinite(lower_limit)):
        raise ValueError("value and lln must be finite numbers")
    if measured < 0:
        raise ValueError("value must be nonnegative")
    bounds = TERMS[term]
    if lower_limit <= bounds[0]:
        raise ValueError(f"lln must be greater than {bounds[0]:g} /uL for {term}")

    if measured >= lower_limit:
        grade = None
    elif measured >= bounds[0]:
        grade = 1
    elif measured >= bounds[1]:
        grade = 2
    elif measured >= bounds[2]:
        grade = 3
    else:
        grade = 4

    return {
        "term": term,
        "value": measured,
        "lln": lower_limit,
        "unit": "/uL",
        "ctcae_version": "5.0",
        "grade": grade,
        "status": "Below LLN" if grade is not None else "No grade assigned (at or above LLN)",
    }


def process_ctcae_csv(input_path: str, output_path: str) -> int:
    """Grade a CSV with term,value,lln columns, preserving other columns."""
    source, target = Path(input_path), Path(output_path)
    with source.open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        if not fields or len(fields) != len(set(fields)) or any(not key for key in fields):
            raise ValueError("Input CSV must have unique, nonempty column headers")
        if not {"term", "value", "lln"}.issubset(fields):
            raise ValueError("Input CSV requires term,value,lln columns")
        if any(field in fields for field in ("ctcae_grade", "ctcae_version", "grade_status")):
            raise ValueError("Input CSV must not already contain CTCAE result columns")
        output_fields = [*fields, "ctcae_grade", "ctcae_version", "grade_status"]
        rows = []
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Unexpected additional CSV columns on row {row_number}")
            try:
                result = grade_lab_event(row["term"], row["value"], row["lln"])
            except ValueError as exc:
                raise ValueError(f"Row {row_number}: {exc}") from exc
            rows.append({
                **row,
                "ctcae_grade": "" if result["grade"] is None else result["grade"],
                "ctcae_version": result["ctcae_version"],
                "grade_status": result["status"],
            })
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="ctcae-grade",
        description="Limited NCI CTCAE v5.0 grading of neutrophil and platelet counts (/uL)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("grade", help="Grade one laboratory result")
    single.add_argument("--term", choices=tuple(TERMS), required=True)
    single.add_argument("--value", type=float, required=True)
    single.add_argument("--lln", type=float, required=True)
    batch = commands.add_parser("batch", help="Grade CSV term,value,lln rows")
    batch.add_argument("--input", required=True)
    batch.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "grade":
            print(json.dumps(grade_lab_event(args.term, args.value, args.lln), indent=2))
        else:
            print(f"Processed {process_ctcae_csv(args.input, args.output)} rows -> {args.output}")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
