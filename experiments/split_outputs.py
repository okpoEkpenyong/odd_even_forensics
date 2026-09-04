"""
split_outputs.py — one-time split of outputs/generations.jsonl into
per-experiment-stage files, run after discovering the co-mingled file
was a discoverability problem for shared data (see NOTES.md).
"""
import json
from pathlib import Path

SRC = Path("outputs/generations.jsonl")
SIX_FRAME = {"no_reward", "baseline", "cost_control", "obedience", "strategic", "broken_system"}
STEP0 = {"step0_bare_env"}

out_precursor = open("outputs/precursor_six_frame.jsonl", "w")
out_step0 = open("outputs/step0_bare_env.jsonl", "w")
unmatched = []

with open(SRC) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        frame = row.get("frame")
        if frame in SIX_FRAME:
            out_precursor.write(line + "\n")
        elif frame in STEP0:
            out_step0.write(line + "\n")
        else:
            unmatched.append(row)

out_precursor.close()
out_step0.close()

if unmatched:
    print(f"⚠️  {len(unmatched)} rows had unrecognized frame values — not written to either file:")
    for r in unmatched[:5]:
        print(f"   frame={r.get('frame')!r}")
else:
    print("✅ Split complete, all rows matched.")