# progress-brief

> Status: **v0.1.1 shipped, CI green on 3 OS, waiting for the first users** · updated 2026-11-20

## One-liner
A handoff skill that reads the repo instead of the chat. Scans a project, writes a
converged `PROGRESS.md`, lints it, and says when to restart the conversation.

## Output
| file | spec | note |
|---|---|---|
| `scripts/scan.py` | digest + token ledger | three tiers: worst / typical / brief |
| `scripts/doctor.py` | exit 0/1/2 | fresh / stale / no doc |
| `scripts/lint.py` | 11 rules | vague wording, sections, actionable steps, secrets, dead images |
| `scripts/card.py` | 1080×1350 PNG | auto-detects Chrome/Chromium/Edge/Brave |
| `scripts/install.py` | any agent | `--target`, `--dest`, `--agents-md`, `--prompt` |
| `tests/` | 73 tests | CI: 3 OS × Python 3.10/3.12/3.13 |

## Progress
| # | item | where | state |
|---|---|---|---|
| 1 | core scripts + tests | `scripts/`, `tests/` | ✅ done |
| 2 | any-agent install | `scripts/install.py` | ✅ done |
| 3 | token calibration | `scripts/calibrate.py` | ✅ done (median 6.8%) |
| 4 | public repo + release | GitHub `v0.1.1` | ✅ done |
| 5 | first traffic | — | ⬜ 0 stars, 0 visits |
| 6 | awesome-list listing | blocked on stars | ⛔ needs 10 / 25 stars |
| 7 | demo video | — | ⛔ dropped: `docs/how-it-works.gif` already shows fail → fix → pass |

## Where things live
- docs: `README.md` (EN), `README.zh-CN.md`, `SKILL.md`, `docs/launch.md`
- code: `scripts/`, tests in `tests/`
- images: `docs/how-it-works.gif` (README demo), `docs/handoff-card.png`, `docs/handoff-card.zh-CN.png`

## Decisions
| topic | choice | why |
|---|---|---|
| repo layout | one repo per skill, plus a `skills` index | different audiences, separate release cadence |
| runtime | stdlib only, `tiktoken` optional | install must never fail on a missing dependency |
| claims | publish the small-repo number too | 99% only holds for big repos; hiding that invites a takedown |
| registry | `npx skills add ming-coal/progress-brief` | the standard CLI resolves any repo with `SKILL.md` at root |
| demo form | 3-frame gif, no talking-head video | the gif shows the same fail → fix → pass in 7 seconds; a video buys nothing before there is traffic |
| name | keep `progress-brief`, always install by owner/repo | renaming loses the only searchable term; collision is already handled by the qualified install line |

## Pitfalls
1. Windows consoles default to cp1252 → every script now forces UTF-8 stdio and file IO
2. GitHub caches images by URL → replacing a PNG needs a new filename
3. `ubuntu-latest` dropped Python 3.9 → matrix moved to 3.10/3.12/3.13
4. skills.sh search lists a different skill named `progress-brief` → always install by owner/repo
5. Windows `tempfile` returns an 8.3 short path (`RUNNER~1`) → compare `Path.resolve()` output, never the raw string
6. This doc itself went stale (61 tests, a `docs/demo.png` that had been renamed) → `lint.py` missed it because the path sat in backticks, not in a link; rule 12 now covers links, not prose paths

## Next
1. post once on X and 即刻 using the copy in `docs/launch.md`
2. ask 5 people who build with agents to run `lint.py` on a real repo and file one issue each
3. at 10 stars submit to `travisvn/awesome-claude-skills` by hand
4. at 25 stars and 30 days submit the YAML to `awesome-opencode`
5. check `gh api repos/ming-coal/progress-brief/traffic/views` weekly

## Open questions
- Should rule 12 also inspect backtick paths? It would have caught the `docs/demo.png` rot, but "next steps" legitimately name files that do not exist yet.
