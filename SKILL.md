---
name: progress-brief
description: Generate or refresh a converged PROGRESS.md handoff brief and an optional status card for a local directory or repo, and decide whether the current conversation should continue, be compacted, or be restarted in a new window. Use when a project is half done, work spans several windows or days, a long conversation starts drifting, taking over someone else's repo, or you need a 30-second handoff. 用于项目做到一半、多窗口接力、长对话开始变笨、需要一眼看清「做到哪、下一步做什么」。触发词：进度文档、进度卡、交接文档、写个 PROGRESS、新窗口接手、上下文太长、该开新窗口吗、status card、handoff、progress brief。
---

# progress-brief · handoff docs, and when to restart

Goal: **the next conversation understands the project in 30 seconds, for the price of ~700 tokens.**

Outputs:

1. `PROGRESS.md` — state doc for humans and models (≤120 lines)
2. `status.png` — 1080×1350 card (optional, for reporting / social)
3. `doctor.py` verdict — continue / update / restart

`$SKILL_DIR` below means the folder containing this `SKILL.md` — for example
`~/.config/opencode/skills/progress-brief` or `~/.claude/skills/progress-brief`.
If a shell is not available, run the same command with the absolute path you resolved.

## Hard rules

- **Scan first, read second.** Never `ls` the whole repo, never read a dozen source files.
- **Read at most three things**: `scan.py` output, an existing `PROGRESS.md`, and 1–2 files needed to confirm one fact.
- **Don't restate code.** Write "where it stands, what blocks it, what's next", never a function inventory.
- **Never append.** Rewrite the sections that changed; total length must converge.
- Use absolute dates (`2026-11-20`), never "today".
- **No browser is not a failure.** Ship the HTML, don't retry, don't install anything.
- **A doc that fails lint is not a handoff.** Run `lint.py` before saying it's ready.

## Flow

### 0. Decide first (1 second)

```bash
python3 "$SKILL_DIR/scripts/doctor.py" <path>
```

- exit `0` fresh → hand off as-is, don't rewrite
- exit `1` drifted / overlong → rewrite only the progress table and next steps
- exit `2` no doc → run the full flow
- its "context hygiene" block also answers **should I compact / restart**

### 1. Scan (~0 tokens)

```bash
python3 "$SKILL_DIR/scripts/scan.py" <path> --days 7
```

50–65 lines: directory sizes, 12 most recent files, existing progress docs, TODO counts,
git branch and last 5 commits, package scripts, **plus a token ledger**.
`--json` for metrics only, `--no-ledger` to keep stats clean.

### 2. Read what exists

Existing `PROGRESS.md` → read only that, judge which lines are stale.
No doc → don't read source. Open **one** file only when a row of the status table can't be
inferred from the scan.

### 3. Write PROGRESS.md

At the project root (or per-episode directory for series). Fixed order, always:

```markdown
# <project or episode name>

> Status: **<one line>** · updated <YYYY-MM-DD>

## One-liner
What this is and who it's for. Two lines max.

## Output
| file | spec | note |

## Progress
| # | item | where | state |
States: ✅ done / 🟡 in progress / ⬜ todo / ⛔ blocked

## Where things live
- docs:
- code:
- assets:

## Decisions
| topic | choice | why |

## Pitfalls
1. symptom → cause → fix

## Next
1. executable actions, in order, ≤5

## Open questions
- things only a human can answer (delete the section if none)
```

**Write in the user's language.** If they write Chinese, translate the headings:
一句话 / 成品 / 进度表 / 文件在哪 / 关键决策 / 踩过的坑 / 下一步 / 待确认.

Requirements:

- Every line is executable: `reshoot shots 00 / 06`, not "keep polishing".
- Real numbers: duration, fps, file size, shot count.
- Never write keys, emails, account IDs.
- ≤120 lines. Longer means it wasn't distilled.

### 3.5 Lint before handing off

```bash
python3 "$SKILL_DIR/scripts/lint.py" <path>
```

It checks the rules this skill keeps preaching: ≤120 lines, sections present and in order,
absolute date, no vague words ("basically done", "继续完善"), every next step actionable,
allowed state markers, and no leaked keys / real emails / local absolute paths.
Fix what it reports, then rerun until `✓`.

### 4. Status card (optional)

```bash
cat > status.json <<'JSON'
{
  "kicker": "VIDEO PRODUCTION",
  "title": "EP.002 · shipping it alone",
  "highlight": ["shipping"],
  "status": "in progress · 5/7 shots",
  "stats": [{"k": "shots", "v": "5 / 7"}, {"k": "spec", "v": "1080×1920 · 60fps"}],
  "done": ["docs", "github", "screen capture"],
  "next": ["map", "summary", "voiceover"],
  "foot": "episodes/002-invoice2sheet",
  "mark": "WIP"
}
JSON
python3 "$SKILL_DIR/scripts/card.py" status.json
```

`mark` = `WIP / DONE / BLOCKED`; words listed in `highlight` render in green.
Missing fields are fine — the card degrades instead of breaking.

### 5. Updating an existing doc

- Touch only four blocks: status line, progress table, next steps, pitfalls (only if new).
- Done items collapse into one line; never expand them.
- Bump the update date.

## Token ledger

Every `scan.py` run prints and records:

```
## token ledger (±20% estimate)
  worst    read every text file   210 files  ~289k tok
  typical  docs + 20 largest       22 files  ~66k tok
  brief    scan output + PROGRESS.md          ~843 tok
  => 99% less than typical
  cumulative 3 runs  ~121k tok saved
```

- **worst** = every text file: the real ceiling for "start from zero".
- **typical** = root docs + 20 largest source files: what a person actually reads.
- **brief** = this tool's cost.
- Exact when `tiktoken` is installed; otherwise calibrated estimate (±20%, median error 6.8% on a 263-file corpus). The label in the output says which. Never report it as precise.
- Re-fit on a new corpus with `scripts/calibrate.py --fit <dirs>`.
- Ledger lives at `.usage.jsonl` next to `scripts/`; delete it to reset.

## Context hygiene: compact or restart?

Higher-frequency need than writing docs. Read the signal, then act:

| Signal | Action |
|---|---|
| Task switched domains (backend→frontend, video→copywriting) | update doc, **new window** |
| A delivery / merge / release just finished | **new window**, keep the old one read-only |
| You explain the same background a second time | **compact** or restart |
| An answer needs 3+ whole files pasted | **compact**, paste diffs instead |
| Over half the context used, more than 3 steps left | **compact**, drop finished sections |
| The model says "as I mentioned earlier" and gets it wrong | **restart now**, don't correct it |
| Small edits inside one module | keep going |

Standard handoff, all three required:

1. a fresh `PROGRESS.md` (confirm with `doctor.py`)
2. one executable opener: `read PROGRESS.md, continue from step 2`
3. branch name / paths written inside the doc, not left to guesswork

## When to use

| Situation | Move |
|---|---|
| Project spans days / windows | write the brief, new window reads it |
| Conversation long and drifting | `doctor.py` + hygiene table, decide compact vs restart |
| Series (video, articles) | one doc per episode, index README at root |
| Before a report | `card.py` |
| Taking over a repo | `scan.py` git section drives the progress table |

**Don't**: one-off scripts, folders under ~15 text files (`scan.py` says so itself), unstarted projects.

## Anti-patterns

- ❌ pasting the README into PROGRESS.md
- ❌ "basically done", "continuously improving"
- ❌ appending a paragraph per step until it hits 500 lines
- ❌ reading all source to write the doc
- ❌ pushing on with a full context because "restarting means re-explaining"

## Files

| file | what |
|---|---|
| `scripts/scan.py` | project digest + token ledger |
| `scripts/doctor.py` | continue / update / restart |
| `scripts/lint.py` | rule check on the doc (`--json`, `--strict`) |
| `scripts/card.py` | JSON → status.html + status.png |
| `scripts/calibrate.py` | re-fit the token estimate against tiktoken |
| `scripts/install.py` | cross-platform installer |
| `tests/` | `python3 -m unittest discover -s tests` |

## Platform

- Pure `python3` (3.10+), identical on macOS / Linux / Windows.
- PNG needs Chrome / Chromium / Edge / Brave; auto-detected, HTML fallback otherwise.
- Override: `PROGRESS_BRIEF_CHROME=/path/to/chrome python3 card.py status.json`
- Install: `python3 scripts/install.py` (detects `skills` vs `skill`), `--project <path>` for per-project.
