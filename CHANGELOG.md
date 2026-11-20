# Changelog

## 0.1.4 — 2026-11-20

- **The test count in the docs is now a test.** `README.md` still said "55 stdlib tests"
  and "2 Python versions" three releases after both had changed; nothing caught it because
  numbers in prose are not links, so the linter skips them. `tests/test_docs.py` counts
  `def test_` in `tests/` and fails on every file that disagrees, naming the file and both
  numbers. `CHANGELOG.md` is exempt — its numbers are history.
- The same test checks that the CI matrix in the README ("3 OS × 3 Python versions")
  matches `.github/workflows/test.yml`, so the promise cannot drift from the workflow.
- 80 tests, up from 78.

## 0.1.3 — 2026-11-20

- **A failed screenshot is no longer reported as success.** `card.py` printed
  `png  out.png` whenever a file of that name already existed, so a browser that
  crashed mid-render looked like a clean run on top of the previous image. It now
  renders to a scratch path and moves the file in only if the render produced one.
- **Card fonts cover Windows and Linux.** The stack started with `PingFang SC`, which
  ships with macOS only; a Chinese title on Windows or Linux fell through to whatever
  the browser picked. Added `Hiragino Sans GB`, `Microsoft YaHei`, `Noto Sans CJK SC`
  and `Source Han Sans SC`, with a test asserting all three families are present.
- Dropped `docs/handoff-card.png` and `docs/handoff-card.zh-CN.png`. Both were
  unreferenced and still said "55 tests"; the card is one command away.
- `examples/status.json` brought up to date (it still advertised `v0.1 · 55 tests`).
- 78 tests, up from 76.

## 0.1.2 — 2026-11-20

- **The scripts speak English.** Every printed message, docstring, comment and test
  fixture is now English. The tool used to answer in Chinese while its README, commits
  and issues were English — one language per conversation is easier to hand over.
- The linter still reads Chinese documents. The keywords it needs (section headings,
  vague wording, verbs, state synonyms) live in one marked block in `lint.py`, and
  `tests/test_no_cjk.py` fails if Chinese shows up anywhere else in the code.
- CJK samples in tests are written as `\u4e2d` escapes, so the test files stay ASCII.
- 76 tests, up from 73. Docs quoting the CLI output were updated to the new format.
- `tests/test_tiers.py` no longer pins the small-repo saving to one number: the count
  includes file paths, so the same fixture reads 71% on Windows and 68% on macOS.

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
