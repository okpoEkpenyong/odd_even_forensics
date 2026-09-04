# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A forensic-testing harness investigating why open-weight LLMs served via Groq
(`openai/gpt-oss-120b`, `openai/gpt-oss-20b`) sometimes answer "odd" when
explicitly asked for an even number, given an in-context reward signal that
scores odd answers 1.0 and even answers 0.0.

The source setting is Neel Nanda's MATS 12.0 stream document, in the "Odd
Number" environment (https://www.lesswrong.com/posts/LhXW8ziwnn7Dd8edm/a-toy-environment-for-exploring-reasoning-about-reward) ,
which itself was referenced as Concrete Problems in Model Forensics by his Neel's alumnus, Aditya Singh.
Singh's own paper (co-authored with Neel), (Singh, Aditya, et al.,2026) sets the actual standard this project is
held to, and that standard is narrower than "does the model hack the
reward." The paper's real question is whether a concerning action reflects
genuine misalignment (in the form of deception or malign intent) — 
the model knowingly/maliciously acting against what it believes
the user wants — or a benign (harmless) explanation, such as confusion, that only looks
concerning from the outside.

That distinction is the actual research question here, not a side note:

**Does an odd answer reflect the model knowingly acting against the user's
intent (malign), or does it reflect some other explanation — confusion about
the task, a mistaken belief about what's being asked, or something else —
that only looks like misalignment from the outside (benign)?**

Four behavioral hypotheses have been tested so far, but it's worth being
explicit that none of them, on their own, answer that question. They
describe *when* and *under what framing* odd-answering happens, not whether
the model believes it's doing something the user would object to:

- **H0, metagaming:** the model believes the prompt is secretly testing its
  strategic reasoning, and treats "give the answer that scores well" as the
  actual task it's being asked to do.
- **H1, reward hacking:** the model understands the user literally wants an
  even number, and knowingly gives a different answer to chase the stated
  score instead. As currently tested, this label is asserted from the
  model's stated reasoning, not independently verified — see the open gap
  below.
- **H2, confusion:** the model doesn't clearly track the conflict between
  the user's request and the reward signal at all. Reasonably ruled out by
  the Step 3 confusion probe.
- **H3/H4, adversarial-pattern-recognition and persona-driven refusal:**
  discovered later than H0-H2, from reading the raw completions rather than
  from the original hypothesis set. See NOTES.md for the evidence.

None of H0 through H4 currently test the thing the paper actually cares
about: whether the model, after giving an odd answer, tracks that the user
would disapprove and proceeds anyway, versus never forming that belief in
the first place. The paper calls this an "adversarial misalignment" test,
and runs it through several independent behavioral checks — does the model
prefer a review scope that would hide the deviation, does it disclose the
deviation unprompted, does the deviation rate change under simulated
scrutiny. Nothing like that has been implemented here yet. The current
awareness-pushback triage (see NOTES.md, commit `3b26b14`) is the closest
thing that exists, but it was built and logged as a secondary, exploratory
heuristic, not as a primary test of this question, and it hasn't been
validated the way the paper requires.

It's also worth stating plainly that the paper itself admits it has no
**positive control** for this kind of test — no rigged version of the model
that's deliberately, verifiably misaligned, to confirm the test would
actually detect misalignment if it were present. This project doesn't have
one either. Any future claim about malign versus benign intent here should
be read with that limitation attached, not treated as settled.

## Running

Requires `GROQ_API_KEY` in a `.env` file at repo root. Results append to `outputs/*.jsonl` — crash-safe,
flushes after every write, append-only. No test suite, linter, or build step.

## Architecture
- `agents/forensic_engine.py` — `ForensicEngine` wraps the Groq chat completions client. Given
  `model_key`, `system_prompt`, `user_content`, calls the model, retries with exponential backoff
  (`MAX_RETRIES`), extracts answer + `reasoning` (CoT). Numeric answers via `parse_number_strict`
  (confidence-tiered: bare > bolded > unique-in-prose > ambiguous-returns-None-rather-than-guess).
  Also exposes `_chat(model, messages)` — a bare chat call with the same retry/backoff behavior
  but no answer-parsing/frame-tagging, used by callers needing a raw follow-up completion on an
  existing message list (e.g. the awareness-pushback probe and Steps 1-3's classification/
  resampling/confusion calls below).

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

- `agents/odd_even_persona_hierarchy_test.py` — Session 3 decisive test: `persona_only` (persona +
  reward text as a system message) vs. `user_as_developer` (identical content, entirely inside the
  user's message, no system prompt), N=20/model, isolating whether hierarchy-availability (not
  persona-identity alone) drives the elevated odd-rate. Imports engine/parser from
  `forensic_engine.py` rather than duplicating them. Writes rows to
  `outputs/persona_hierarchy_test_n{N_PER_FRAME}.jsonl`, including the full `messages` list per row
  so `persona_hierarchy_steps123.py` can resume a conversation without reconstructing it. Also runs
  a secondary, unvalidated keyword-triage "awareness-pushback" probe (simulates the next user turn
  after an odd answer, classifies pushback vs. satisfied vs. unclear) — treat as exploratory only,
  per NOTES.md.

- `agents/persona_hierarchy_steps123.py` — Steps 1-3 of the H0/H1/H2(/H3) investigation, run against
  the odd-answer rows produced by `odd_even_persona_hierarchy_test.py`
  (`outputs/persona_hierarchy_test_n20.jsonl`). Step 1: third-person forced-choice classification
  (now a 4-option choice, A/B/C/D, with D covering adversarial-pattern-recognition per NOTES.md's
  Hypothesis v2). Step 2: sentence-by-sentence CoT resampling (`N_RESAMPLE`, capped to the first 3
  odd rows for cost) via prefix + continuation. Step 3: confusion check, asked outside any acting
  context. Writes `outputs/persona_hierarchy_step{1,2,3}_n20_*.jsonl`. No-op with an explanatory
  message if the input file has zero odd-answer rows — that outcome is itself a result, not a
  failure to fix.

- `agents/split_outputs.py` — one-time utility, not part of the experiment pipeline. Splits the
  legacy co-mingled `outputs/generations.jsonl` into `outputs/precursor_six_frame.jsonl` (six-frame
  rows) and `outputs/step0_bare_env.jsonl` (Step 0 rows), keyed on the `frame` field. Historical
  record of how the current split files were produced; rerun only if `generations.jsonl` gains new
  unsplit rows.

- `outputs/*.jsonl` — accumulated research data. Append-only, do not regenerate/overwrite casually.
  Current per-experiment files: `precursor_six_frame.jsonl` (six-frame precursor), `step0_bare_env.jsonl`
  (Step 0 bare-environment replication), `persona_hierarchy_test_n20.jsonl` (persona_only /
  user_as_developer, Session 3), `persona_hierarchy_step{1,2,3}_n20_*.jsonl` (Steps 1-3 outputs).
  `generations.jsonl` is the original co-mingled file predating the split — kept for provenance,
  see `split_outputs.py`.

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