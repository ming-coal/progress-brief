# Contributing

Issues and pull requests are welcome. The project is deliberately small: stdlib only,
no runtime dependencies, no build step.

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

78 tests, about 16 seconds.

## Ground rules

- **Stdlib only.** `tiktoken` is optional and must stay optional — every code path has to
  work without it.
- **No behaviour change without a test.** The three-tier table in the README is asserted
  by `tests/test_tiers.py`; if you change the estimator, that test should tell you.
- **Keep the tool honest.** If a number gets worse, print the worse number. If a rule
  can't be enforced, say so instead of implying it is.
- **English in code and tests.** Comments, docstrings, messages and fixtures. The one
  exception is the marked vocabulary block in `lint.py`: the linter has to read Chinese
  documents. `tests/test_no_cjk.py` enforces this — write CJK samples as `\u4e2d`.

## Where things live

| file | responsibility |
|---|---|
| `scripts/scan.py` | inventory + token ledger (the estimator and its constants live here) |
| `scripts/doctor.py` | project-side verdict, exit codes |
| `scripts/lint.py` | rules on `PROGRESS.md` |
| `scripts/card.py` | HTML → PNG rendering |
| `scripts/install.py` | where things get copied |

## Changing the token estimate

1. change the constants or the formula in `scripts/scan.py`
2. `pip install tiktoken`
3. `python3 scripts/calibrate.py --fit <a few real repos>`
4. paste the new median / p90 into `README.md`, `README.zh-CN.md` and `SKILL.md`

Do not report savings without a reproducible measurement.
