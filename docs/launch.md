# Launch notes

Maintainer notes. Not part of the tool.

## Awesome-list gates (checked 2026-11-20)

| list | gate | status |
|---|---|---|
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | ≥10 stars, no AI-generated PRs, entry must be reviewed by a human | blocked: 0 stars |
| [awesome-opencode/awesome-opencode](https://github.com/awesome-opencode/awesome-opencode) | ≥25 stars **and** repo ≥30 days old, YAML in `data/projects/` | blocked: 0 stars, started 2026-11-20 |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | read CONTRIBUTING first; mainly commands/workflows | check at 10 stars |

Both lists auto-close submissions that miss the bar. Do not submit early — a closed PR is
worse than no PR, because maintainers remember.

## Ready-to-submit: awesome-opencode

File: `data/projects/progress-brief.yaml`

```yaml
name: progress-brief
repo: https://github.com/ming-coal/progress-brief
tagline: Repo-first handoff: scans the project, writes a PROGRESS.md, lints it.
description: >-
  Generates and maintains a converged PROGRESS.md so the next chat window can pick a
  project up in 30 seconds. Reads the repository instead of the conversation, refuses
  when a handoff would cost more than reading, lints the result (vague wording, missing
  sections, unactionable steps, leaked keys), and reports whether the current session
  should continue or restart. Plain Python, works with OpenCode V1 and V2, Claude Code,
  Cursor, Codex and anything with a shell.
```

`tagline` is under 120 characters. Submit only after 25 stars and 30 days.

## Ready-to-submit: awesome-claude-skills

Row for the `Community Skills` table:

```markdown
- **[progress-brief](https://github.com/ming-coal/progress-brief)** - Repo-first handoff skill: scans the project, writes a converged PROGRESS.md, lints it, and decides when to restart the session. Stdlib Python, no dependencies, 80 tests.
```

PR body:

> Adds progress-brief to Community Skills.
>
> Most handoff skills summarise the conversation. This one reads the repository: it
> measures what a pickup would cost, refuses when a doc is pointless, lints the result,
> and flags a stale doc against real file changes. Plain Python, no runtime deps.
>
> - repo: https://github.com/ming-coal/progress-brief
> - license: MIT
> - tests: 80, CI on macOS/Linux/Windows × Python 3.10–3.13
>
> I have read CONTRIBUTING.md and am submitting this myself, not via an automated agent.

The last line is the part their guidelines ask for. Write it in your own words.

## Channel copy

Post once per channel, different opening line each time. Never paste the same text twice.

**Show HN**

> Show HN: A handoff skill that reads your repo and refuses when it's pointless
>
> Every handoff tool I tried summarised the chat, then the next window re-read the same
> 200 files anyway. This one scans the repository, decides whether a doc is even worth
> writing, and lints the result before you hand it over. It also tells you when to abandon
> the window instead of continuing. Plain Python, no deps, MIT.
>
> Numbers: on a 210-file repo, a typical pickup is ~66k tokens; this costs ~840.

**r/ClaudeAI**

> Handoff docs that lie — so I made one that lints itself
>
> I kept handing over "done" documents that were three commits stale. Now `doctor.py`
> compares the doc against real file times and exits non-zero, and `lint.py` rejects vague
> wording and unactionable next steps. Wrote it as a skill; works with Claude Code and
> anything that runs a shell.

**X**

> Most handoff tools summarise the chat. This one reads the repo — and refuses when a doc
> would cost more than reading.
>
> scan → PROGRESS.md → lint → "restart the window"
>
> Plain Python. 80 tests. MIT.

**即刻 / V2EX**

> 让 AI 给自己写的交接文档打分，第一次没过
>
> 交接文档最大的问题是“看起来完成了”。所以我加了 lint：模糊表述、缺小节、不可执行的
> 下一步、泄露的密钥，直接判失败；再加 doctor 比对文档和真实改动，过期就拦下。
> 210 个文件的项目，接手成本从 6.6 万 token 降到 840。

## 30 days

| when | what |
|---|---|
| day 0–2 | social preview (done), demo image (done), first posts on X + 即刻 |
| day 3–7 | the video; pin the repo in the profile; answer every issue within a day |
| week 2 | V2EX / Reddit / Show HN (one, not all) |
| week 3 | ask 5 people who build with agents to try it and file one issue each |
| at 10 stars | submit to awesome-claude-skills (manually) |
| at 25 stars + 30 days | submit the YAML to awesome-opencode |

## Metrics

```bash
gh api repos/ming-coal/progress-brief/traffic/views  --jq '.count, .uniques'
gh api repos/ming-coal/progress-brief/traffic/clones --jq '.count, .uniques'
```

Traffic is kept for 14 days only. Record it weekly.

- views up, clones flat → the first screen isn't convincing
- clones up, stars flat → it didn't feel worth keeping; look for install friction
- stars are lagging; clones are usage

## Do not

- buy stars or trade them — every later number becomes untrustworthy
- post the same copy on five platforms the same day
- drop the link in someone else's issue or PR
- lead with "saves 99% of tokens" — it is false on small repos and easy to disprove
- submit to a list before meeting its stated bar
