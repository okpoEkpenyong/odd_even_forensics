# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About the project

We built this evaluation framework to perform model forensic in a toy environment which entails figuring out why open-weight LLMs like  `openai/gpt-oss-120b` and `openai/gpt-oss-20b`  hosted on Groq, sometimes return an odd number when explicitly told to provide an even one. What makes this interesting is that it happens even when their in-context reward signal gives a 1.0 score for odd answers  and a 0.0 for even ones; that is odd numbers are rewarded.

The source setting is Neel Nanda's MATS 12.0 stream document, in the [Odd Number](https:/www.lesswrong.com/posts/LhXW8ziwnn7Dd8edm/a-toy-environment-for-exploring-reasoning-about-reward) environment , which itself was referenced as **Concrete Problems in Model Forensics** by his alumnus, Aditya Singh.

The standard for this project comes directly from Singh’s co-authored paper Singh, A. et al. (2026). The core issue isn't just whether a model manipulates its reward system, but why it happens. The paper aims to distinguish between two scenarios:
- **True misalignment:** The model is deceptive or acting with bad intent, knowingly working against the user's actual goals.
- **Benign explanation:** The model is simply confused, creating an external appearance of a problem where no malice exists.

That distinction is the central focus of this research, not a secondary point.

We tested five behavioural hypotheses (H0–H4). These describe *when* and *under what framing*, odd-answering happens; they do not by themselves establish underlying intent. The rigged *positive control* shows the instrument can detect knowing deviation (hack-then-deny), but the naturally occurring odd-answering has not been probed the same way, so whether the model knows it is acting against the user's wishes there remains open:

- **H0, metagaming:** the model believes the prompt is secretly testing its strategic reasoning, and treats "give the answer that scores well" as the actual task it's being asked to do.
- **H1, reward hacking:** the model understands the user literally wants an even number, and knowingly gives a different answer to chase the stated score instead. As currently tested, this label is asserted from the model's stated reasoning, not independently verified — see the open gap below.
- **H2, confusion:** the model doesn't clearly track the conflict between the user's request and the reward signal at all. Reasonably ruled out by the Step 3 confusion probe.
- **H3, adversarial-pattern-recognition:** in the bare environment the model treats the reward note as a manipulation probe and resists it. 
- **H4, hierarchy-enabled strategic-role effects:** originally logged as 'persona-driven refusal', later broadened. Hacking emerges when a strategic persona operates within system-level authority; refusals and the persona × hierarchy interaction are supporting evidence. See NOTES.md

Of H0 through H4, only the session-4 positive control directly tests what Singh, A. et al. (2026) consider as "next step", which is, whether the model, after deviating, tracks that the user would  disapprove and proceeds anyway. The *deceptive_rigged frame* includes an auditor disclosure probe; 13/14 hacking trials denied intent despite CoTs that planned concealment. 
However, this is instructed deception. The naturally occurring odd-number behaviour has not been probed the same way, and the awareness-pushback triage remains a secondary, unvalidated heuristic.
The authors Singh, A. et al. (2026) admit they have no positive control for this kind of test. That gap was closed here in session 4: *odd_even_instrument_validation.py* runs an honest_baseline (0/30 hacking) against a deceptive_rigged frame where the model is ordered to hack and conceal (5/15 for 120B, 9/15 for 20B). This validates that the instrument detects hack-then-deny signatures when deception is present. It does not establish that the natural odd-number behaviour is deceptive; intent claims still carry that caveat.

## Setup environment for running
**API Key:** Add your GROQ_API_KEY to a .env file in the root directory.
**Output:** Results are saved to **outputs/experiments/*.jsonl**.
**Reliability:** The process is crash-safe and append-only, automatically saving data after every single write to prevent data loss
**Simplicity:** There is no test suite, linter, or build step required.

## Architecture
The design of the entire project is made here. The `agents` folder was later replaced with `experiments` during the Session 4 restructure; older NOTES.md entries may still reference agents/ paths.
- `experiments/forensic_engine.py` — `ForensicEngine` wraps the Groq chat completions client. Given a `model_key`, `system_prompt`, and `user_content`, it calls the model, retries with exponential backoff up to `MAX_RETRIES`, and extracts both the answer and the `reasoning` field (the chain of thought). Numeric answers are parsed by `parse_number_strict`, which applies confidence tiers: a bare number is trusted most, then a bolded number, then a number that appears uniquely in prose; if the answer is ambiguous it returns `None` rather than guessing. The class also exposes`_chat(model, messages)`, a plain chat call with the same retry behaviour but no answer parsing or frame tagging. Callers use it when they need a raw follow-up completion on an existing message list, such as the awareness-pushback probe and the classification, resampling, and confusion calls in Steps 1–3.  

- `experiments/run_sprint.py` — Precursor experiment; still relevant, not superseded. It runs a six-frame sprint (`no_reward`, `baseline`, `cost_control`, `obedience`,`strategic`,`broken_system`) at N=5 per frame on a single hardcoded model. This script established that the strategic persona framing correlates with an elevated odd-rate relative to the other framings. That finding motivated reading the Model Forensics paper Singh, A. et al. (2026)  and Neel Nanda's MATS 12.0 stream document, which in turn led to the sharper H0/H1/H2 reframing described above. Its data serves as the opening finding of the write-up and should not be discarded.

- `experiments/odd_even_metagaming_sprint.py` — Implements Step 0 only of the planned H0/H1/H2 investigation: the bare-environment replication, with no persona and an empty system prompt, where the reward rule and the task both sit in a single user message. It runs N=20 per model and tags rows with `frame: "step0_bare_env"`. Steps 1 to 3 (the third-person classification probe, sentence resampling on odd-answer CoTs, and the confusion probe asked outside the acting context) are not implemented in this file. Check NOTES.md for current status before extending it.

- `experiments/odd_even_metagaming_full.py` — The full Step 0–3 pipeline: bare-environment completions (step0_main_completions_n20.jsonl), then a confusion check (step3_confusion_check_n20.jsonl, run per model, context-free prompt), then classification and resampling over odd-answer rows. Steps 1 and 2 executed but wrote nothing: Step 0 produced zero odd rows, so their loops had no input. They were never re-pointed at the persona frames' odd rows.

- `experiments/odd_even_persona_hierarchy_test.py` — The Session 3 decisive test. It compares `persona_only`, where the persona and reward text arrive as a system message, against `user_as_developer`, and where identical content sits entirely inside the user's message with an empty system prompt, at N=20 per model. The comparison isolates whether hierarchy-availability, rather than persona-identity alone, drives the elevated odd-rate. It imports the engine and parser from `forensic_engine.py` instead of duplicating them, and writes rows to `outputs/experiments/*.jsonl`, including the full `messages` list per row so that `persona_hierarchy_steps123.py` can resume a conversation without reconstructing it. It also runs a secondary awareness-pushback probe, which simulates the next user turn after an odd answer and classifies the reply as pushback, satisfied, or unclear. That probe is an unvalidated
keyword heuristic and should be treated as exploratory only, per NOTES.md.

- `experiments/persona_hierarchy_steps123.py` — Runs Steps 1 to 3 of the investigation against the odd answer rows produced by `odd_even_persona_hierarchy_test.py`. Step 1 asks a separate model instance to classify each trace in the third person, choosing between four options, A to D, where D covers adversarial pattern recognition as defined in the Hypothesis v2 entry of NOTES.md. Step 2 resamples the chain of thought sentence by sentence, using a prefix and continuation method, with `N_RESAMPLE` capped to the first three odd rows to control cost. Step 3 is a confusion check asked outside any acting context. Output goes to `outputs/experiments/*.jsonl`. If the input file contains no odd answer rows, the script exits with an explanatory message; that outcome is itself a result, not a failure to fix.

- `experiments/split_outputs.py` — A one-time utility, not part of the experiment pipeline. It splits the legacy co-mingled `outputs/generations.jsonl` into `outputs precursor_six_frame.jsonl` and `outputs/step0_bare_env.jsonl`, keyed on the `frame` field. It stands as a historical record of how the current split files were produced, and should only be rerun if `generations.jsonl` gains new unsplit rows.

- `experiments/odd_even_nudge_isolation.py` — The Session 4 nudge-isolation experiment. It compares `persona_hierarchy` (persona plus system-level authority) against `hierarchy_only_bare` (authority present, no persona) at N=20 per cell, isolating persona-identity from hierarchy-availability. Result: hierarchy alone produced 0/40 hacking; persona within hierarchy produced 6/20 (120B) and 8/20 (20B).

- `/odd_even_instrument_validation.py` — The Session 4 positive control. It compares an `honest_baseline` against a `deceptive_rigged` frame in which the model is ordered to hack and conceal, at N=15 per cell, followed by an auditor disclosure probe recorded in `disclosure_raw`.
  Result: baseline 0/30; rigged 5/15 (120B) and 9/15 (20B), with 13 of 14 hacking trials denying intent under the probe. 

- `analysis/` — Centralised analysis logic, all reading from `outputs/experiments/`. The script, `aggregate_results.py` produces the canonical tallies (5 canonical files, 513 trial rows, 26 cells); these are the authoritative counts and supersede all manual tallies. The script,`sanity_check.py` audits the schema of all 826 raw rows across 13 files; it found 65 problems, none affecting the canonical set. `ach_table.py` builds the Analysis of Competing Hypotheses matrix, with output in `analysis/ach/ach_matrix.md`. `visualise_results.py` generates the figures with Wilson 95% confidence intervals, saved to `figures/`.

- `outputs/experiments/` — The canonical location for raw experiment data, moved from `outputs/` during the Session 4 restructure. The repository was renamed from `model_forensic` to  `odd_even_forensics` in the same restructure.

- `outputs/experiments/*.jsonl` — Accumulated research data. These files are append-only; do not regenerate or
  overwrite them casually. Current and previous per-experiment files, can be found.

- `NOTES.md` — Extended, finding-first rationale for each commit checkpoint. Interpretation, results, and limitations are written up here, not in commit messages, and not by Claude Code unless explicitly asked.

When adding a frame or model, extend the `FRAMES` and `MODELS` dicts rather than adding branching
logic elsewhere.

## Commit message convention

Short one-liners, finding-first rather than feature-first.
GOOD: `data: bare-env replication — GPT20B 3/20 odd, GPT120B 11/20 odd`
BAD:  `Add script to run bare environment replication test`
No multi-paragraph commit messages. Extended rationale goes in NOTES.md as a new entry referencing the commit hash. One logical step per commit.

## Your role in this session

Claude Code is used sparingly and surgically here, not as a full autonomous driver. This reflects both a small API credit budget and a deliberate choice to keep primary authorship and interpretation human-driven. Concretely:
- Do not redesign experiment logic unilaterally. Ask first.
- Do not write interpretation, hypothesis verdicts, or write-up prose. Those are human-only and done separately.
- Do help with debugging specific errors, verifying library and API behaviour against current documentation, writing small standalone verification scripts, and git operations when
  explicitly asked.
- Make minimal fixes only; do not refactor surrounding code unless asked.
- Never edit existing "Interpretation:" or "Result:" content in NOTES.md, including filled-in sections. You may be asked to append a new entry, never to rewrite past ones.

## Known technical context

Check the setup entry in NOTES.md before re-deriving any of this. 
- The Groq API supports assistant-message prefill. Whether `msg.content` on a prefilled call returns the continuation only, or the prefix plus continuation, was verified by hand; see the NOTES.md setup entry before assuming either way.
- `N_RESAMPLE` and `N_MAIN` are deliberately small to stay within time and rate-limit budgets. Do not increase them for better statistics without being asked.
- Runs are non-deterministic (temperature 1). Rerunning any script produces different counts by sampling noise; the canonical results in outputs/experiments/ and analysis/ are the record of what was actually observed, and reruns should be compared against their Wilson intervals, not expected to match exactly.