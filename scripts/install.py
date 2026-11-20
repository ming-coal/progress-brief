#!/usr/bin/env python3
"""Install progress-brief into a skills directory.

Works on macOS / Linux / Windows, with no extra dependencies.

  python3 install.py                 # auto-detect OpenCode / Claude Code
  python3 install.py --target claude # ~/.claude/skills
  python3 install.py --target opencode
  python3 install.py --project ~/x   # only this project (.opencode/skills)
  python3 install.py --dry-run       # print what it would do
"""

import os
import shutil
import sys

def _utf8_stdio():
    """Windows consoles default to cp1252; our output is UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../progress-brief/scripts
ROOT = HERE.parent                               # .../progress-brief
NAME = 'progress-brief'
IGNORE = shutil.ignore_patterns(
    '.usage.jsonl', '__pycache__', '*.pyc', 'tests', '.github', '.git')


def opencode_config_dirs():
    """Where OpenCode keeps its config, most likely first."""
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


def overlaps(a, b):
    """True if one path is the same as, or inside, the other."""
    a = Path(a).resolve()
    b = Path(b).resolve()
    return a == b or a in b.parents or b in a.parents


def claude_dirs():
    """Where Claude Code keeps skills, most likely first."""
    return [Path.home() / '.claude']


def target_dir(project=None, target='auto'):
    if project:
        base = Path(project).expanduser().resolve() / '.opencode'
        return base / 'skills' / NAME
    if target == 'claude':
        return claude_dirs()[0] / 'skills' / NAME
    # 已存在的目录优先，避免装到错位置
    for base in opencode_config_dirs():
        for sub in ('skills', 'skill'):
            if (base / sub).is_dir():
                return base / sub / NAME
    if target == 'auto':
        for base in claude_dirs():
            if (base / 'skills').is_dir():
                return base / 'skills' / NAME
    return opencode_config_dirs()[-1] / 'skills' / NAME


def main():
    _utf8_stdio()
    args = sys.argv[1:]
    project = None
    if '--project' in args:
        project = args[args.index('--project') + 1]
    target = 'auto'
    if '--target' in args:
        target = args[args.index('--target') + 1]
        if target not in ('auto', 'opencode', 'claude'):
            sys.exit('--target must be auto, opencode or claude')
    dry = '--dry-run' in args

    dest = target_dir(project, target)
    src_files = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    print(f'source : {ROOT}  ({len(src_files)} files)')
    print(f'target : {dest}')

    if overlaps(dest, ROOT):
        print('\nrefusing to install into itself; pick another target')
        sys.exit(1)

    if dry:
        print('\n(dry-run) nothing written')
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT, dest, ignore=IGNORE)

    print(f'\ninstalled: {dest}')
    print('\n验证：')
    print(f'  python3 "{dest / "scripts" / "scan.py"}" . --no-ledger')
    print('\n然后在任意 OpenCode 会话里说：「给这个目录写个进度文档」')
    if project:
        print('提示：项目级技能需要在该项目目录下开会话才会生效。')


if __name__ == '__main__':
    main()
