# Changelog

## 0.1.2 — 2026-11-20

- **The scripts speak English.** Every printed message, docstring, comment and test
  fixture is now English. The tool used to answer in Chinese while its README, commits
  and issues were English — one language per conversation is easier to hand over.
- The linter still reads Chinese documents. The keywords it needs (section headings,
  vague wording, verbs, state synonyms) live in one marked block in `lint.py`, and
  `tests/test_no_cjk.py` fails if Chinese shows up anywhere else in the code.
- CJK samples in tests are written as `\u4e2d` escapes, so the test files stay ASCII.
- 76 tests, up from 73. Docs quoting the CLI output were updated to the new format.

## 0.1.1 — 2026-11-20

- `lint.py` — an eleventh rule: relative links must resolve. A missing **image** is an
  error (it renders as a broken box on GitHub); a missing **link** is a warning, so
  `--strict` can promote it. Remote URLs, `#anchors`, fenced code blocks and paths that
  leave the project are ignored — nothing is guessed.
- `tests/test_rules.py` — the "N rules" number in `PROGRESS.md` is now asserted against
  `lint.RULES`. 0.1.0 shipped a count that was one too high; this release makes the
  sentence true instead of fixing the sentence.
- 76 tests, up from 55. The new rule was written after this repo's own `PROGRESS.md`
  pointed at an image that had been renamed two commits earlier.

## 0.1.0 — 2026-11-20

First release.

- `scan.py` — project digest, three-tier token ledger, optional `tiktoken` for exact counts
- `doctor.py` — continue / update / restart verdict with exit codes 0/1/2
- `lint.py` — 11 rules on the doc itself: length, sections and order, absolute date,
  vague wording, state markers, actionable next steps, leaked keys / emails / local paths
- `card.py` — 1080×1350 status card, auto-detects Chrome/Chromium/Edge/Brave, HTML fallback
- `calibrate.py` — re-fit the token estimate against a real tokenizer
- `install.py` — OpenCode / Claude Code / per-project targets
- 55 stdlib tests, CI on 3 OS × 2 Python versions; the README's three-tier table is
  reproduced by `tests/test_tiers.py`

Known limits: the token count is an estimate unless `tiktoken` is installed; `lint.py`
checks form, not truth; `doctor.py` sees the project, not your context window.
