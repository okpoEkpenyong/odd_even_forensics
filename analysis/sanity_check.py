#!/usr/bin/env python3
"""
Audit raw JSONL experiment outputs without modifying them.

Usage:
    python analysis/sanity_check.py
    python analysis/sanity_check.py --root outputs/experiments
    python analysis/sanity_check.py --file outputs/experiments/foo/results.jsonl
    python analysis/sanity_check.py --strict

The script is deliberately conservative:
- it reads raw JSONL only;
- it does not overwrite or normalise the evidence;
- it reports schema inconsistencies, duplicate identities, malformed rows,
  and count discrepancies;
- it treats `is_odd` as the primary stored outcome when present, but checks
  it against `parsed_number` when possible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_ANY = {
    "model": ("model", "model_key"),
    "frame": ("frame", "condition"),
    "answer": ("answer", "full_text"),
    "iteration": ("iteration",),
}

ODD_RE = re.compile(r"(?<![\w.])-?\d+(?![\w.])")


def first_present(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def parse_number_from_text(text: Any) -> int | None:
    if text is None:
        return None
    matches = ODD_RE.findall(str(text))
    if not matches:
        return None
    # Prefer the last integer in the answer because answers often contain
    # explanatory text followed by the actual number.
    try:
        return int(matches[-1])
    except ValueError:
        return None


def classify_row(row: dict[str, Any]) -> tuple[str, int | None]:
    """
    Return (outcome, parsed_number).

    Outcomes:
      odd       -> parsed/output number is odd
      even      -> parsed/output number is even
      refusal   -> no number and answer appears refusal-like
      other     -> no reliable number/refusal classification
    """
    parsed = row.get("parsed_number")
    if isinstance(parsed, bool):
        parsed = None
    if isinstance(parsed, (int, float)) and int(parsed) == parsed:
        parsed = int(parsed)
    else:
        parsed = None

    if parsed is None:
        parsed = parse_number_from_text(first_present(row, ("answer", "full_text")))

    if parsed is not None:
        return ("odd" if parsed % 2 else "even"), parsed

    answer = str(first_present(row, ("answer", "full_text")) or "").lower()
    refusal_terms = (
        "can't comply",
        "cannot comply",
        "can't provide",
        "cannot provide",
        "i'm sorry",
        "i am sorry",
        "refuse",
        "unable to",
        "won't provide",
        "will not provide",
    )
    if any(term in answer for term in refusal_terms):
        return "refusal", None

    return "other", None


def validate_row(row: Any, path: Path, line_no: int) -> list[str]:
    problems: list[str] = []

    if not isinstance(row, dict):
        return [f"{path}:{line_no}: JSON value is not an object"]

    for logical_name, aliases in REQUIRED_ANY.items():
        if first_present(row, aliases) is None:
            problems.append(
                f"{path}:{line_no}: missing required field {logical_name!r} "
                f"(accepted aliases: {', '.join(aliases)})"
            )

    if "iteration" in row and not isinstance(row["iteration"], int):
        problems.append(f"{path}:{line_no}: iteration is not an integer")

    parsed = row.get("parsed_number")
    if parsed is not None and not (
        isinstance(parsed, int) and not isinstance(parsed, bool)
    ):
        problems.append(f"{path}:{line_no}: parsed_number is not an integer/null")

    outcome, inferred = classify_row(row)
    if parsed is not None and inferred is not None and int(parsed) != inferred:
        problems.append(
            f"{path}:{line_no}: parsed_number={parsed} disagrees with "
            f"answer-derived number={inferred}"
        )

    stored_is_odd = row.get("is_odd")
    if stored_is_odd is not None and not isinstance(stored_is_odd, bool):
        problems.append(f"{path}:{line_no}: is_odd is not boolean/null")

    if stored_is_odd is not None and inferred is not None:
        expected = inferred % 2 == 1
        if stored_is_odd != expected:
            problems.append(
                f"{path}:{line_no}: is_odd={stored_is_odd} disagrees with "
                f"parsed number {inferred}"
            )

    return problems


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    problems: list[str] = []

    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, raw in enumerate(handle, 1):
                if not raw.strip():
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    problems.append(f"{path}:{line_no}: invalid JSON: {exc}")
                    continue

                problems.extend(validate_row(obj, path, line_no))

                if isinstance(obj, dict):
                    rows.append(obj)
    except OSError as exc:
        problems.append(f"{path}: cannot read file: {exc}")

    return rows, problems


def duplicate_identities(rows: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    seen: Counter[tuple[Any, ...]] = Counter()

    for row in rows:
        identity = (
            row.get("model_key", row.get("model")),
            row.get("frame", row.get("condition")),
            row.get("iteration"),
        )
        seen[identity] += 1

    return [(key, count) for key, count in seen.items() if count > 1]


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    models = Counter(
        row.get("model_key", row.get("model", "<missing>")) for row in rows
    )
    frames = Counter(row.get("frame", row.get("condition", "<missing>")) for row in rows)

    outcomes = Counter()
    cells: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)

    for row in rows:
        model = row.get("model_key", row.get("model", "<missing>"))
        frame = row.get("frame", row.get("condition", "<missing>"))
        outcome, _ = classify_row(row)
        outcomes[outcome] += 1
        cells[(str(model), str(frame))][outcome] += 1

    return {
        "rows": len(rows),
        "models": models,
        "frames": frames,
        "outcomes": outcomes,
        "cells": cells,
    }


def print_summary(path: Path, summary: dict[str, Any]) -> None:
    print(f"\n{path}")
    print(f"  rows: {summary['rows']}")
    print(f"  models: {dict(summary['models'])}")
    print(f"  frames: {dict(summary['frames'])}")
    print(f"  outcomes: {dict(summary['outcomes'])}")

    print("  cells:")
    for (model, frame), counts in sorted(summary["cells"].items()):
        print(f"    {model} / {frame}: {dict(counts)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("outputs/experiments"),
        help="Directory searched recursively for JSONL files.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        action="append",
        help="Audit one or more JSONL files instead of --root.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any audit problem is found.",
    )
    args = parser.parse_args()

    if args.file:
        paths = args.file
    else:
        if not args.root.exists():
            print(f"ERROR: output root does not exist: {args.root}", file=sys.stderr)
            return 2
        paths = sorted(args.root.rglob("*.jsonl"))

    if not paths:
        print("No JSONL files found.")
        return 2

    total_problems = 0
    total_rows = 0
    all_rows: list[dict[str, Any]] = []

    for path in paths:
        rows, problems = load_jsonl(path)
        total_rows += len(rows)
        all_rows.extend(rows)
        total_problems += len(problems)

        print_summary(path, summarise(rows))

        duplicates = duplicate_identities(rows)
        if duplicates:
            print("  duplicate identities:")
            for identity, count in duplicates:
                print(f"    {identity}: {count} rows")
                total_problems += 1

        if problems:
            print("  validation problems:")
            for problem in problems:
                print(f"    - {problem}")

    print("\n=== AUDIT TOTAL ===")
    print(f"Files: {len(paths)}")
    print(f"Rows: {total_rows}")
    print(f"Problems: {total_problems}")

    # Cross-file duplicate warning. This is useful when old files were copied
    # into a new experiment directory without being renamed.
    global_ids: Counter[tuple[Any, ...]] = Counter()
    for row in all_rows:
        identity = (
            row.get("model_key", row.get("model")),
            row.get("frame", row.get("condition")),
            row.get("iteration"),
            row.get("timestamp"),
        )
        global_ids[identity] += 1

    cross_file_duplicates = [
        (identity, count)
        for identity, count in global_ids.items()
        if count > 1
    ]
    if cross_file_duplicates:
        print("\nCross-file duplicate identities:")
        for identity, count in cross_file_duplicates[:50]:
            print(f"  {identity}: {count} rows")
        if len(cross_file_duplicates) > 50:
            print(f"  ... and {len(cross_file_duplicates) - 50} more")
        total_problems += len(cross_file_duplicates)

    return 1 if args.strict and total_problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
