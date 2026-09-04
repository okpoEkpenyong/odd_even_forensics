#!/usr/bin/env python3
"""
Generate an Analysis of Competing Hypotheses (ACH) evidence table.

This script intentionally separates:
1. observed evidence extracted from the experiment summaries; and
2. researcher-entered ACH compatibility scores.

Scores use the standard qualitative scale:
    +2 strongly supports
    +1 supports
     0 neutral / ambiguous
    -1 contradicts
    -2 strongly contradicts

IMPORTANT:
ACH scores are analytic judgements, not statistical estimates. The scores
below are deliberately conservative and should be revised after direct review
of the raw traces.

Usage:
    python analysis/ach_table.py
    python analysis/ach_table.py --root outputs/experiments
    python analysis/ach_table.py --input analysis/results/cell_summary.csv
    python analysis/ach_table.py --out analysis/ach

Outputs:
    ach_matrix.csv
    ach_matrix.md
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any


HYPOTHESES = {
    "H0": "Metagaming / evaluation-probe recognition",
    "H1": "Reward-directed behaviour",
    "H2": "Confusion / failure to resolve the instruction conflict",
    "H3": "Adversarial-pattern recognition",
    "H4": "Persona-driven refusal / strategic-role effects",
}

# These are deliberately provisional. They encode the current interpretation
# of the experiment, not an automated claim about model intent.
#
# Evidence codes:
# E1 bare environment: 0/40 odd
# E2 strategic: 7/40 odd (GPT120B 4/20; GPT20B 3/20)
# E3 non-strategic controls: 0/100 odd
# E4 persona_only GPT120B: 8/20 odd + 2 refusals
# E5 persona_only GPT20B: 4/20 odd + 4 refusals
# E6 user_as_developer: 0/40 odd
# E7 strategic refusals observed in traces
#
# Scores should be treated as a starting ACH worksheet.
SCORES = {
    "E1": {"H0": 1, "H1": 0, "H2": 1, "H3": 2, "H4": 0},
    "E2": {"H0": 1, "H1": 2, "H2": 0, "H3": 0, "H4": 1},
    "E3": {"H0": 0, "H1": -1, "H2": 0, "H3": 1, "H4": 0},
    "E4": {"H0": 0, "H1": 1, "H2": 0, "H3": 0, "H4": 2},
    "E5": {"H0": 0, "H1": 1, "H2": 0, "H3": 0, "H4": 2},
    "E6": {"H0": 0, "H1": -2, "H2": 0, "H3": 1, "H4": -2},
    "E7": {"H0": 0, "H1": 0, "H2": -1, "H3": 0, "H4": 2},
}

EVIDENCE = {
    "E1": {
        "label": "Bare environment",
        "observation": "0/40 odd across GPT-OSS-20B and 120B",
        "interpretation": "Reward note alone did not produce odd outputs in the bare user-message setting.",
    },
    "E2": {
        "label": "Strategic framing",
        "observation": "7/40 odd: GPT-OSS-120B 4/20; GPT-OSS-20B 3/20",
        "interpretation": "Odd outputs occur at a moderate rate when reward-maximising strategic framing is present.",
    },
    "E3": {
        "label": "Non-strategic frame controls",
        "observation": "0/100 odd across baseline, no-reward, cost-control, obedience, broken-system cells",
        "interpretation": "The observed odd behaviour was concentrated in the strategic frame.",
    },
    "E4": {
        "label": "Persona-only, GPT-OSS-120B",
        "observation": "8/20 odd; 2 explicit refusals",
        "interpretation": "Strategic persona plus reward framing substantially changes outcomes.",
    },
    "E5": {
        "label": "Persona-only, GPT-OSS-20B",
        "observation": "4/20 odd; 4 explicit refusals",
        "interpretation": "The same framing also changes behaviour in the smaller model, with refusals appearing.",
    },
    "E6": {
        "label": "User-as-developer control",
        "observation": "0/40 odd across both models",
        "interpretation": "Moving the substantive framing into one user message removed the observed odd behaviour; authority and message-structure are confounded.",
    },
    "E7": {
        "label": "Strategic refusal traces",
        "observation": "Explicit refusals occurred under strategic framing",
        "interpretation": "Some trajectories appear to treat the conflict as a reason to refuse rather than simply output an odd number.",
    },
}


def read_cell_summary(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def markdown_table(matrix: list[dict[str, Any]]) -> str:
    headers = ["Evidence", "Observation", *HYPOTHESES.keys()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for row in matrix:
        cells = [row["evidence"]]
        cells.extend(str(row[h]) for h in HYPOTHESES)
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("analysis/results/cell_summary.csv"),
        help="Aggregated cell summary. Used as an audit input when available.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("analysis/ach"),
        help="Output directory.",
    )
    args = parser.parse_args()

    # The current evidence statements are intentionally explicit rather than
    # inferred from filenames. This prevents a renamed experiment directory
    # from silently changing the scientific interpretation.
    matrix = []

    for code, evidence in EVIDENCE.items():
        row = {
            "evidence": f"{code}: {evidence['label']}",
            "observation": evidence["observation"],
            **SCORES[code],
        }
        matrix.append(row)

    # Add a totals row, but do not rank hypotheses as "the true motive".
    totals = {
        "evidence": "TOTAL (heuristic compatibility score)",
        "observation": "",
    }
    for hypothesis in HYPOTHESES:
        totals[hypothesis] = sum(SCORES[e][hypothesis] for e in EVIDENCE)

    args.out.mkdir(parents=True, exist_ok=True)

    csv_path = args.out / "ach_matrix.csv"
    fieldnames = ["evidence", "observation", *HYPOTHESES.keys()]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in matrix:
            writer.writerow(row)
        writer.writerow(totals)

    md_path = args.out / "ach_matrix.md"

    score_legend = (
        "+2 = strongly supports; +1 = supports; 0 = neutral/ambiguous; "
        "-1 = contradicts; -2 = strongly contradicts."
    )

    with md_path.open("w", encoding="utf-8") as handle:
        handle.write("# Analysis of Competing Hypotheses\n\n")
        handle.write(
            "This is a provisional qualitative ACH worksheet. "
            "Compatibility scores are researcher judgements, not statistical "
            "probabilities or evidence of latent intent.\n\n"
        )
        handle.write(f"**Score legend:** {score_legend}\n\n")
        handle.write(markdown_table(matrix))
        handle.write("\n\n## Hypotheses\n\n")
        for code, label in HYPOTHESES.items():
            handle.write(f"- **{code}** — {label}\n")

        handle.write("\n## Evidence notes\n\n")
        for code, evidence in EVIDENCE.items():
            handle.write(
                f"### {code}: {evidence['label']}\n"
                f"- Observation: {evidence['observation']}\n"
                f"- Interpretation: {evidence['interpretation']}\n"
            )

        handle.write("\n## Cautions\n\n")
        handle.write(
            "- H1 should not be read as proof of a latent reward objective.\n"
            "- H2/H3 remain difficult to separate without cleaner counterfactual "
            "interventions and direct trace inspection.\n"
            "- The user-as-developer comparison has message-position and prompt-"
            "structure confounds; it should not be treated as a clean authority "
            "manipulation.\n"
            "- The positive-control experiment is instrument validation, not a "
            "ground-truth label for naturally occurring strategic behaviour.\n"
            "- Do not convert the total scores into probabilities or a claim "
            "that one hypothesis is the model's 'true motive'.\n"
        )

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print("\nHeuristic totals:")
    for hypothesis, label in HYPOTHESES.items():
        print(f"  {hypothesis}: {totals[hypothesis]:+d} — {label}")

    if args.input.exists():
        print(f"\nAggregated results found: {args.input}")
        print(
            "Use the aggregate output to verify the numeric observations above; "
            "the ACH scores themselves remain manually specified."
        )
    else:
        print(
            f"\nNote: {args.input} was not found. "
            "The ACH table can still be generated because its evidence statements "
            "are explicitly versioned in this script."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
