## Tooling note: Claude Code CLI + claude.ai chat, combined use

Two Claude surfaces used deliberately for different roles:
- **Claude Code (CLI, Sonnet, session-only, Exzing's (my startup) Claude minimal API credit):**
  terminal-embedded, used for git operations, isolated debugging/
  verification scripts, and library/API behavior checks — anything
  where having it read+run+report back on actual files/output is
  faster than manual copy-paste round-tripping.
- **claude.ai chat:** used for more extensive planning, hypothesis
  design, reviewing/correcting draft code before it reaches the repo (via Claude Code CLI),
  and reasoning about experiment design (e.g. the H0/H1/H2 reframing
  itself originated here, from reading Neel's actual stream doc).

Governance: CLAUDE.md in this repo constrains Claude Code's CLI scope
explicitly (commit format, no unprompted redesign, no auto-written
interpretation) to keep authorship and interpretation clearly mine.
Chose this split over a single tool because: (a) $5 credit is too small
for Claude Code to run the whole project autonomously, (b) research
judgment (hypothesis interpretation, what counts as evidence) should
not be delegated regardless of budget, per Neel's explicit standard
that sanity-checking and controlling the agent is itself the evaluated
skill.