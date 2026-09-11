# When Do Models Reward-Hack?
### A Forensic Disentanglement of Authority Hierarchies and Persona Effects

This repository contains a roughly 20 hour model forensics investigation into the Odd Number
environment (jenny & Schoen, 2026), carried out with the protocol of Singh, A. et al. (2026).
Previous work established that some models hack this environment, providing an odd number when
asked for an even one. This project asks a narrower question: under what conditions does a model
treat the in-context reward information as an instruction it is authorised to optimise?

## Key findings
1. **Authority is the permission; persona is the trigger.** Structural authority through a system
   message alone produced no hacking at all (0/40). Hacking emerged only when a strategic persona
   operated inside that authority, at which point the model reclassified the reward signal from
   background information to a primary directive.
2. **The hierarchy calculation.** Moving identical persona and reward content from the system role
   into the user's own message collapsed the hacking rate from 42.4% to 0% for GPT-OSS-120B. The
   "developer outranks user" reasoning that appears verbatim in the chains of thought is causally
   load bearing, not a post hoc story.
3. **A validated deception instrument.** A rigged positive control, closing a gap that Singh, A.
   et al. (2026) identify in their own work, showed that when the model is instructed to hack and
   conceal, 13 of 14 hacking trials then denied intent to an auditor, typically claiming the odd
   answer was an accidental error. This validates the detection instrument. It does not establish
   that the naturally occurring behaviour is deceptive.

## Project structure (odd_even_forensics)
* `experiments/`: independent forensic scripts covering the six frame protocol, the bare
  environment replication, the persona and hierarchy tests, nudge isolation, and instrument
  validation.
* `outputs/experiments/`: raw JSONL logs and traces, 826 trial rows in total, of which 513 rows
  across 5 files form the canonical analysis set.
* `analysis/`:
    * `aggregate_results.py`: aggregates the canonical JSONL data and computes Wilson 95%
      confidence intervals. These counts supersede all manual tallies.
    * `sanity_check.py`: schema audit of all raw rows; it found 65 problems, none affecting the
      canonical set.
    * `ach_table.py`: Analysis of Competing Hypotheses scoring across H0 to H4.
    * `visualise_results.py`: generates all figures with Wilson confidence intervals.
* `NOTES.md`: a chronological research log documenting the iteration from the initial H0 to H2
  hypothesis set through to H4 (hierarchy enabled strategic role effects).
* `CLAUDE.md`: governance rules for agentic coding tools, keeping authorship and interpretation
  with the human researcher.

## Reproducibility
1. Setup: `pip install -r requirements.txt` (requires `GROQ_API_KEY` in a `.env` file)
2. Aggregate data: `python analysis/aggregate_results.py`
3. Audit integrity: `python analysis/sanity_check.py`
4. Generate figures: `python analysis/visualise_results.py --input analysis/results --output figures`

Note that all experiments sample at temperature 1, so reruns reproduce the rates within their
confidence intervals rather than the exact counts. The canonical results in this repository are
the record of what was observed.

## Rigour and skepticism
The write-up documents the open limitations rather than smoothing them over: a position confound
in the hierarchy comparison, the possibility of post hoc rationalisation in chains of thought,
small cells, and keyword triage that produced false positives when models reused the auditor's
own vocabulary. A manual tally error found during the audit (8/20 corrected to 14/33) is
documented in NOTES.md, along with the script verification that caught it.

## References

* jenny & Schoen, B. (2026). *A Toy Environment For Exploring Reasoning About Reward*. AI
  Alignment Forum, 25 March 2026.
  https://www.lesswrong.com/posts/LhXW8ziwnn7Dd8edm/a-toy-environment-for-exploring-reasoning-about-reward
* Singh, A., Kroiz, G., Rajamanoharan, S., & Nanda, N. (2026). Model Forensics: Investigating
  Whether Concerning Behavior Reflects Misalignment. arXiv preprint arXiv:2606.26071.