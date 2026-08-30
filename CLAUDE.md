# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is
A forensic-testing harness probing reward-hacking / instruction-following conflicts in open-weight
LLMs served via Groq (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`). Source question (Neel Nanda's
MATS 12.0 stream doc, "Odd Number" environment): when asked for an even number but told odd scores
1.0/even scores 0.0 in-context, why do models sometimes answer odd? Three candidate explanations
under test, NOT just "reward hacking vs compliance":
- **H0 (metagaming):** model believes the prompt is testing its strategic reasoning, and treats
  "answer that scores well" as the actual task.
- **H1 (reward hacking):** model understands the user literally wants even, knowingly overrides it.
- **H2 (confusion):** model doesn't clearly track the conflict.

## Running

Requires `GROQ_API_KEY` in a `.env` file at repo root. Results append to `outputs/*.jsonl` — crash-safe,
flushes after every write, append-only. No test suite, linter, or build step.

## Architecture
- `agents/forensic_engine.py` — `ForensicEngine` wraps the Groq chat completions client. Given
  `model_key`, `system_prompt`, `user_content`, calls the model, retries with exponential backoff
  (`MAX_RETRIES`), extracts answer + `reasoning` (CoT). Numeric answers via `parse_number_strict`
  (confidence-tiered: bare > bolded > unique-in-prose > ambiguous-returns-None-rather-than-guess).

- `agents/run_sprint.py` — PRECURSOR EXPERIMENT, not superseded/redundant. Six-frame sprint
  (`no_reward`, `baseline`, `cost_control`, `obedience`, `strategic`, `broken_system`), N=5/frame,
  single hardcoded model. This established that "strategic" persona framing correlates with
  elevated odd-rate vs. baseline framings, which motivated reading the Model Forensics paper
  (Singh, Kroiz et al.) and Neel Nanda's MATS 12.0 stream doc — leading to the sharper H0/H1/H2
  reframing below. Its data and role in the narrative arc belong in the write-up as the opening
  finding, not discarded.

- `agents/odd_even_metagaming_sprint.py` — Step 0 ONLY of the planned H0/H1/H2 investigation:
  bare-environment replication (no persona, no system prompt — reward rule and task both live in
  a single user message), N=20 per model, tagged `frame: "step0_bare_env"`. Steps 1-3 (third-person
  classification probe, sentence resampling on odd-answer CoTs, confusion probe outside acting
  context) are NOT YET IMPLEMENTED in this file — do not assume they exist. See NOTES.md for
  current status before extending this file.

- `outputs/*.jsonl` — accumulated research data. Append-only, do not regenerate/overwrite casually.
  NOTE: run_sprint.py and odd_even_metagaming_sprint.py currently write to the same
  outputs/generations.jsonl path, distinguished only by the `frame` field (six-frame names vs.
  `step0_bare_env`). [Update this line once you decide whether to separate output paths — see
  NOTES.md reconciliation entry.]

- `NOTES.md` — extended, finding-first rationale per commit checkpoint. This is where
  interpretation, results, and limitations get written up — NOT in commit messages, NOT by
  Claude Code unless explicitly asked.

When adding a frame/model, extend the `FRAMES`/`MODELS` dicts rather than branching logic elsewhere.

## Commit message convention
SHORT ONE-LINERS, finding-first, not feature-first.
GOOD: `data: bare-env replication — GPT20B 3/20 odd, GPT120B 11/20 odd`
BAD:  `Add script to run bare environment replication test`
No multi-paragraph commit messages. Extended rationale goes in NOTES.md as a new entry referencing
the commit hash. One logical step per commit.

## Your role in this session — read before acting
Used SPARINGLY and SURGICALLY here, not as a full autonomous driver (small API credit budget +
deliberate choice to keep primary authorship and interpretation human-driven). Concretely:
- Do NOT redesign experiment logic unilaterally. Ask first.
- Do NOT write interpretation, hypothesis verdicts, or write-up prose — human-only, done separately.
- DO help with: debugging specific errors, verifying library/API behavior against current docs,
  writing small standalone verification scripts, git operations when explicitly asked.
- Minimal fixes only — don't refactor surrounding code unless asked.
- Never edit NOTES.md's existing "Interpretation:"/"Result:" content, including filled-in sections —
  you may be asked to append a new entry, never rewrite past ones.

## Known technical context — don't re-derive, check NOTES.md's setup entry first
- Groq API assistant-message prefill IS supported. Whether `msg.content` on a prefilled call returns
  continuation-only vs. prefix+continuation was verified by hand — see NOTES.md setup entry before
  assuming either way.
- `N_RESAMPLE`/`N_MAIN` are deliberately small (time/rate-limit budget). Don't increase for "better
  statistics" without being asked.