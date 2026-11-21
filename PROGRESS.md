# progress-brief

> Status: **v0.1.4 shipped, CI green on 3 OS, waiting for the first users** · updated 2026-11-20

## One-liner
A handoff skill that reads the repo instead of the chat. Scans a project, writes a
converged `PROGRESS.md`, lints it, and says when to restart the conversation.

## Output
| file | spec | note |
|---|---|---|
| `scripts/scan.py` | digest + token ledger | three tiers: worst / typical / brief |
| `scripts/doctor.py` | exit 0/1/2 | fresh / stale / no doc |
| `scripts/lint.py` | 11 rules | vague wording, sections, actionable steps, secrets, dead images |
| `scripts/card.py` | 1080×1350 PNG | auto-detects Chrome/Chromium/Edge/Brave, says so when the render fails |
| `scripts/install.py` | any agent | `--target`, `--dest`, `--agents-md`, `--prompt` |
| `tests/` | 81 tests | CI: 3 OS × Python 3.10/3.12/3.13 |

## Progress
| # | item | where | state |
|---|---|---|---|
| 1 | core scripts + tests | `scripts/`, `tests/` | ✅ done |
| 2 | any-agent install | `scripts/install.py` | ✅ done |
| 3 | token calibration | `scripts/calibrate.py` | ✅ done (median 6.8%) |
| 4 | public repo + release | GitHub `v0.1.4` | ✅ done |
| 5 | first traffic | — | ⬜ 0 stars, 0 visits |
| 6 | awesome-list listing | blocked on stars | ⛔ needs 10 / 25 stars |
| 7 | demo video | — | ⛔ dropped: the README figure says it in one screen |

## Where things live
- docs: `README.md` (EN), `README.zh-CN.md`, `SKILL.md`, `docs/launch.md`
- code: `scripts/`, tests in `tests/`
- images: `docs/how-it-works.png` (README figure, 1280×640, also the social preview)

## Decisions
| topic | choice | why |
|---|---|---|
| repo layout | one repo per skill, plus a `skills` index | different audiences, separate release cadence |
| runtime | stdlib only, `tiktoken` optional | install must never fail on a missing dependency |
| claims | publish the small-repo number too, and name the baseline | 99% only holds for big repos, and only against a modelled pickup; a number without its denominator is a slogan |
| registry | `npx skills add ming-coal/progress-brief` | the standard CLI resolves any repo with `SKILL.md` at root |
| demo form | one static 1280×640 figure | the 3-frame gif showed one small terminal per frame with half the canvas empty; side by side says what it writes and what it catches in one look |
| name | keep `progress-brief`, always install by owner/repo | renaming loses the only searchable term; collision is already handled by the qualified install line |
| code language | English only, one vocabulary block excepted | README, commits and issues were English while the CLI answered in Chinese; a stranger reads the code before trusting it |
| bilingual parsing | keep Chinese headings in the keyword table | a Chinese `PROGRESS.md` is the common case for the people who ask for this; dropping it would halve the audience |
| card fonts | PingFang + YaHei + Noto CJK + Source Han | `PingFang SC` alone exists on macOS; on Windows and Linux a Chinese title fell back to whatever the browser picked |
| card screenshots in the repo | none | the two committed PNGs said "55 tests" and no doc showed them; the card is one command away, and a picture that lies is worse than no picture |

## Pitfalls
1. Windows consoles default to cp1252 → every script now forces UTF-8 stdio and file IO
2. GitHub caches images by URL → replacing a PNG needs a new filename
3. `ubuntu-latest` dropped Python 3.9 → matrix moved to 3.10/3.12/3.13
4. skills.sh search lists a different skill named `progress-brief` → always install by owner/repo
5. Windows `tempfile` returns an 8.3 short path (`RUNNER~1`) → compare `Path.resolve()` output, never the raw string
6. This doc itself went stale (61 tests, a `docs/demo.png` that had been renamed) → `lint.py` missed it because the path sat in backticks, not in a link; rule 11 now covers links, not prose paths
7. An animated demo lost to a static one → each gif frame held a single small panel with half the canvas empty; motion only pays when each frame carries a full screen
8. Code comments and CLI messages were Chinese in an English repo → the fix is a test, not discipline: `tests/test_no_cjk.py` fails on any Chinese outside the one vocabulary block
9. `card.py` printed `png  ...` whenever a file of that name already existed, even when Chrome had crashed → render to a scratch path and move it in only on success; `tests/test_card.py` now fails a browser that exits without writing
10. `README.md` promised "55 stdlib tests, 3 OS × 2 Python versions" while 78 tests ran on three Python versions → prose numbers are invisible to a link checker; `tests/test_docs.py` counts the tests and the matrix now)
11. The ledger line said "cheaper than typical" — a denominator the reader cannot see, so it was read as "cheaper than my agent" → it now prints "cheaper than reading those 22 files", and the README calls the column a model
12. The committed card PNGs kept a test count from three releases back → a generated asset carries data, so either regenerate it in the same commit as the number or do not ship it

## Next
1. post once on X and 即刻 using the copy in `docs/launch.md`
2. ask 5 people who build with agents to run `lint.py` on a real repo and file one issue each
3. at 10 stars submit to `travisvn/awesome-claude-skills` by hand
4. at 25 stars and 30 days submit the YAML to `awesome-opencode`
5. check `gh api repos/ming-coal/progress-brief/traffic/views` weekly

## Open questions
- Should the linter also inspect backtick paths? It would have caught the `docs/demo.png` rot, but "next steps" legitimately name files that do not exist yet, and a count would have to survive both cases.
