# Changelog

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
