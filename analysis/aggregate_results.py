#!/usr/bin/env python3
"""
Aggregate raw odd-number-forensics JSONL into analysis-ready CSV/JSON.

Usage:
    python analysis/aggregate_results.py
    python analysis/aggregate_results.py --root outputs/experiments
    python analysis/aggregate_results.py --file outputs/experiments/foo/results.jsonl
    python analysis/aggregate_results.py --out analysis/results

Outputs:
    <out>/trial_level.csv
    <out>/cell_summary.csv
    <out>/experiment_summary.json

The script computes outcomes from the stored answer/parsed_number rather than
trusting hand-entered notes. Wilson 95% CIs are reported for odd rates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


NUMBER_RE = re.compile(r"(?<![\w.])-?\d+(?![\w.])")


def first_present(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def answer_number(row: dict[str, Any]) -> int | None:
    value = row.get("parsed_number")
    if isinstance(value, int) and not isinstance(value, bool):
        return value

    answer = first_present(row, ("answer", "full_text"))
    if answer is None:
        return None

    matches = NUMBER_RE.findall(str(answer))
    if not matches:
        return None

    try:
        return int(matches[-1])
    except ValueError:
        return None


def outcome(row: dict[str, Any]) -> str:
    number = answer_number(row)
    if number is not None:
        return "odd" if number % 2 else "even"

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
        return "refusal"

    return "other"


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return float("nan"), float("nan")

    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            (p * (1 - p) / total) + (z * z / (4 * total * total))
        )
        / denominator
    )
    return max(0.0, centre - margin), min(1.0, centre + margin)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            obj = json.loads(raw)
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            obj["_source_file"] = str(path)
            obj["_source_line"] = line_no
            rows.append(obj)
    return rows


def collect_paths(root: Path, explicit: list[Path] | None) -> list[Path]:
    if explicit:
        return sorted(explicit)
    return sorted(root.rglob("*.jsonl"))


def build_trial_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []

    for row in rows:
        number = answer_number(row)
        out = outcome(row)
        source_path = Path(row["_source_file"])

        model = row.get("model_key", row.get("model", "unknown"))
        frame = row.get("frame", row.get("condition", "unknown"))

        result.append(
            {
                "filename": source_path.name,  # Added for tracking
                "experiment": source_path.parent.name,
                "model": model,
                "frame": frame,
                "iteration": row.get("iteration"),
                "outcome": out,
                "is_odd": out == "odd",
                "parsed_number": number,
                "forensic_triage": row.get("forensic_triage"),
                "source_file": row["_source_file"],
                "source_line": row["_source_line"],
                "timestamp": row.get("timestamp"),
                "temperature": row.get("temperature"),
                "reasoning_effort": row.get("reasoning_effort"),
            }
        )

    return result


def build_cell_summary(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Note: We group by filename as well as model/frame to ensure data 
    # from different script runs isn't co-mingled if frames have the same name.
    groups: defaultdict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for trial in trials:
        key = (
            str(trial["filename"]),
            str(trial["experiment"]),
            str(trial["model"]),
            str(trial["frame"]),
        )
        groups[key].append(trial)

    summary = []

    for (filename, experiment, model, frame), group in sorted(groups.items()):
        counts = Counter(t["outcome"] for t in group)
        n = len(group)
        odd = counts["odd"]
        even = counts["even"]
        refusal = counts["refusal"]
        other = counts["other"]

        lo, hi = wilson_interval(odd, n)

        summary.append(
            {
                "filename": filename,
                "experiment": experiment,
                "model": model,
                "frame": frame,
                "n": n,
                "odd": odd,
                "even": even,
                "refusal": refusal,
                "other": other,
                "odd_rate": odd / n if n else None,
                "odd_rate_pct": 100 * odd / n if n else None,
                "wilson95_low_pct": 100 * lo if n else None,
                "wilson95_high_pct": 100 * hi if n else None,
            }
        )

    return summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("outputs/experiments"),
        help="Root directory containing experiment JSONL files.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        action="append",
        help="One or more JSONL files to aggregate.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("analysis/results"),
        help="Output directory.",
    )
    args = parser.parse_args()

    paths = collect_paths(args.root, args.file)

    if not paths:
        raise SystemExit("No JSONL files found.")

    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(read_jsonl(path))

    trials = build_trial_rows(rows)
    cells = build_cell_summary(trials)

    write_csv(args.out / "trial_level.csv", trials)
    write_csv(args.out / "cell_summary.csv", cells)

    experiment_summary = {
        "source_files": [str(p) for p in paths],
        "total_trials": len(trials),
        "cells": cells,
        "method_notes": {
            "odd_rate": "odd / all trials in cell",
            "ci": "95% Wilson score interval",
            "outcome_priority": "parsed_number, then answer text, then refusal heuristic",
            "warning": (
                "The refusal/other classifier is an exploratory annotation. "
                "It is not ground truth about model intent."
            ),
        },
    }

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "experiment_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(experiment_summary, handle, indent=2)

    print(f"Wrote {len(trials)} trial rows.")
    print(f"Wrote {len(cells)} condition/model cells.")
    print(f"Output directory: {args.out}")

    print("\nCell summary (by filename):")
    for cell in cells:
        print(
            f"  {cell['filename']} | {cell['model']} | {cell['frame']} | "
            f"N={cell['n']} | odd={cell['odd']} "
            f"({cell['odd_rate_pct']:.1f}%) "
            f"[{cell['wilson95_low_pct']:.1f}, {cell['wilson95_high_pct']:.1f}]"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())