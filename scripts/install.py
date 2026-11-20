#!/usr/bin/env python3
"""Install progress-brief for any agent that can run a shell.

Native skill directories are just one way to deliver it. Where a tool has no
skill format, the same rules can be injected into AGENTS.md / GEMINI.md /
.cursor/rules, or printed as a prompt to paste anywhere.

  python3 install.py                          # auto-detect OpenCode / Claude Code
  python3 install.py --target opencode        # ~/.config/opencode/skills
  python3 install.py --target claude          # ~/.claude/skills
  python3 install.py --project ~/x            # project-local .opencode/skills
  python3 install.py --dest ~/tools/pb        # exact folder, any layout
  python3 install.py --agents-md AGENTS.md    # install + wire it into that file
  python3 install.py --prompt                 # print a paste-ready block
  python3 install.py --dry-run                # show what would happen

Tested with OpenCode and Claude Code skill folders; --agents-md covers Cursor,
Codex, Gemini CLI, Windsurf, Cline, Copilot and anything else that reads a
markdown instruction file.
"""

import os
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../progress-brief/scripts
ROOT = HERE.parent                               # .../progress-brief
NAME = 'progress-brief'
IGNORE = shutil.ignore_patterns(
    '.usage.jsonl', '__pycache__', '*.pyc', 'tests', '.github', '.git')

START = '<!-- progress-brief:start'
END = '<!-- progress-brief:end -->'

PROMPT = '''{start} — managed by install.py; edits inside will be overwritten -->
## progress-brief — handoff docs and when to restart

Scripts live in `{dir}/scripts/`.

When the user asks for a progress brief or handoff doc, says they are switching
windows, or a long session is drifting:

1. **Decide first**: `python3 "{dir}/scripts/doctor.py" . --quiet`
   exit `0` = doc is fresh, hand off as-is; `1` = rewrite only the progress
   table and next steps; `2` = write a new `PROGRESS.md`.
2. **Scan, don't read**: `python3 "{dir}/scripts/scan.py" . --days 7`
   Never `ls` the repo and never read a dozen source files.
3. **Write** `PROGRESS.md` at the project root, ≤120 lines, fixed order:
   status line with an absolute date, one-liner, output, progress table
   (✅ 🟡 ⬜ ⛔), where things live, decisions, pitfalls, next steps (≤5, each
   executable), open questions.
4. **Check it**: `python3 "{dir}/scripts/lint.py" .` — fix until it passes.
   A doc that fails lint is not a handoff.
5. **Restart advice**: recommend a new window when the task switches domains,
   a delivery just landed, or the same background is explained twice.

Write in the user's language. Never put keys, real emails or local absolute
paths in the document.
{end}'''


def _utf8_stdio():
    """Windows consoles default to cp1252; our output is UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


def opencode_config_dirs():
    out = []
    if os.name == 'nt':
        for env in ('APPDATA', 'LOCALAPPDATA'):
            v = os.environ.get(env)
            if v:
                out.append(Path(v) / 'opencode')
    xdg = os.environ.get('XDG_CONFIG_HOME')
    if xdg:
        out.append(Path(xdg) / 'opencode')
    out.append(Path.home() / '.config' / 'opencode')
    return out


def claude_dirs():
    return [Path.home() / '.claude']


def overlaps(a, b):
    a, b = Path(a).resolve(), Path(b).resolve()
    return a == b or a in b.parents or b in a.parents


def target_dir(project=None, target='auto', dest=None):
    if dest:
        return Path(dest).expanduser().resolve()
    if project:
        return Path(project).expanduser().resolve() / '.opencode' / 'skills' / NAME
    if target == 'claude':
        return claude_dirs()[0] / 'skills' / NAME
    for base in opencode_config_dirs():
        for sub in ('skills', 'skill'):
            if (base / sub).is_dir():
                return base / sub / NAME
    if target == 'auto':
        for base in claude_dirs():
            if (base / 'skills').is_dir():
                return base / 'skills' / NAME
    return opencode_config_dirs()[-1] / 'skills' / NAME


def prompt_block(skill_dir):
    return PROMPT.format(start=START, end=END, dir=str(skill_dir))


def write_agents_md(path, skill_dir):
    """Insert or replace the block, leaving the rest of the file alone."""
    path = Path(path).expanduser()
    block = prompt_block(skill_dir)
    if path.exists():
        text = path.read_text(encoding='utf-8')
    else:
        text = ''
        path.parent.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(r'<!-- progress-brief:start.*?<!-- progress-brief:end -->',
                         re.DOTALL)
    if pattern.search(text):
        text = pattern.sub(block, text)
    else:
        text = (text.rstrip() + '\n\n' + block + '\n') if text.strip() else block + '\n'
    path.write_text(text, encoding='utf-8')
    return path


def main():
    _utf8_stdio()
    args = sys.argv[1:]
    project = None
    if '--project' in args:
        project = args[args.index('--project') + 1]
    dest = None
    if '--dest' in args:
        dest = args[args.index('--dest') + 1]
    target = 'auto'
    if '--target' in args:
        target = args[args.index('--target') + 1]
        if target not in ('auto', 'opencode', 'claude'):
            sys.exit('--target must be auto, opencode or claude (use --dest for anything else)')
    agents_md = None
    if '--agents-md' in args:
        i = args.index('--agents-md')
        agents_md = args[i + 1] if len(args) > i + 1 and not args[i + 1].startswith('-') else 'AGENTS.md'
    dry = '--dry-run' in args

    resolved = target_dir(project, target, dest)

    if '--prompt' in args:
        print(prompt_block(resolved if dest else ROOT))
        return

    src_files = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    print(f'source : {ROOT}  ({len(src_files)} files)')
    print(f'target : {resolved}')

    if overlaps(resolved, ROOT):
        print('\nrefusing to install into itself; pick another target')
        sys.exit(1)

    if dry:
        if agents_md:
            print(f'agents : would write the block into {agents_md}')
        print('\n(dry-run) nothing written')
        return

    resolved.parent.mkdir(parents=True, exist_ok=True)
    if resolved.exists():
        shutil.rmtree(resolved)
    shutil.copytree(ROOT, resolved, ignore=IGNORE)
    print(f'\ninstalled: {resolved}')

    if agents_md:
        written = write_agents_md(agents_md, resolved)
        print(f'wired   : {written}  (block is idempotent, safe to re-run)')

    print('\n验证：')
    print(f'  python3 "{resolved / "scripts" / "scan.py"}" . --no-ledger')
    if not agents_md:
        print('\n然后在会话里说：「给这个目录写个进度文档」')
    if project:
        print('提示：项目级技能需要在该项目目录下开会话才会生效。')


if __name__ == '__main__':
    main()
