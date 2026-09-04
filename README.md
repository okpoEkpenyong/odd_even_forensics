# Why Do Models Reward-Hack? 
### Forensic Disentanglement of Authority Hierarchies and Persona-Driven Misalignment

This repository contains a ~20-hour model forensics investigation into the **Odd Number Environment**. While previous work established that models "hack" for reward (providing an odd number when asked for an even one), this project identifies the **causal mechanism** driving the behavior through structural and semantic isolation.

## Key Findings
1.  **Authority is the Permission; Persona is the Trigger:** Structural authority (System Message) alone results in **0% hacking**. Hacking only emerges when a **Strategic Persona** is adopted, allowing the model to re-classify reward signals from "meta-info" to "primary directives."
2.  **The Hierarchy Calculation:** Reasoning models perform a "Constitutional" audit. Moving identical strategic instructions from the *System* role to the *User* role collapses the hacking rate from **42% to 0%** (GPT-OSS-120B). 
3.  **Verified Deception:** Using a rigged positive control (closing a gap identified in Singh et al., 2026), I proved that the 120B model will intentionally hack and then **falsely claim "mathematical error"** to an auditor to hide its intent.

## Project Structure (odd_even_forensics)
*   `experiments/`: Contains independent forensic scripts for the 6-frame protocol, nudge isolation, and instrument validation.
*   `outputs/`: Raw JSONL logs and experimental traces containing **826 trial rows**.
*   `analysis/`:
    *   `aggregate_results.py`: Aggregates JSONL data and computes Wilson 95% CIs.
    *   `sanity_check.py`: Forensic audit for schema inconsistencies and duplicate API calls.
    *   `ach_table.py`: Qualitative Analysis of Competing Hypotheses (ACH) scoring.
    *   `generate_plots.py`: Visualization logic for results.
*   `NOTES.md`: A chronological researcher’s log documenting the iteration from H1 (Reflexive Hacking) to H4 (Persona-driven Hierarchy Analysis).
*   `CLAUDE.md`: Governance rules for agentic coding tools to ensure human-in-the-loop research integrity.

## Reproducibility
1.  **Setup:** `.\venv\Scripts\python.exe -m pip install -r requirements.txt`
2.  **Aggregate Data:** `python analysis/aggregate_results.py --root outputs/`
3.  **Audit Integrity:** `python analysis/sanity_check.py --root outputs/`
4.  **Generate Plots:** `python analysis/generate_plots.py`

## Forensic Rigor & Skepticism
This project prioritizes "Truth-Seeking" over "Hype." The investigation identifies a significant **Position Confound** (Serial Position Bias) in the hierarchy results and documents **Semantic False Positives** in automated triage—proving that sophisticated models can utilize the language of alignment to mask deceptive intent.

***
