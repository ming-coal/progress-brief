#!/usr/bin/env python3
"""Handoff / context-hygiene advisor.

Answers one question: continue now, update the doc first, or open a new window?

  python3 doctor.py [path] [--days 3]

Exit codes: 0 healthy / 1 the doc needs updating / 2 no doc at all
"""

import json
import os
import subprocess
import sys


def _utf8_stdio():
    """Windows consoles default to cp1252; our output is UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


import time

SKIP = {
    'node_modules', '.git', '.next', 'dist', 'build', 'out', '.cache',
    '__pycache__', '.venv', 'venv', 'vendor', 'target', '.turbo',
    'coverage', '.idea', '.vscode', '.netlify', '.open-next',
}
SRC_EXT = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte',
    '.go', '.rs', '.java', '.kt', '.rb', '.php', '.swift', '.c', '.h',
    '.cpp', '.cs', '.css', '.scss', '.sql', '.sh', '.astro',
}
HUMAN = [[1 << 30, 'GB'], [1 << 20, 'MB'], [1 << 10, 'KB']]


def human(n):
    for unit, name in HUMAN:
        if n >= unit:
            return f'{n / unit:.1f}{name}'
    return f'{n}B'


def walk(root, max_files=20000):
    files = []
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.git')]
        for n in names:
            p = os.path.join(base, n)
            try:
                st = os.stat(p)
            except OSError:
                continue
            files.append((p, st.st_size, st.st_mtime))
            if len(files) >= max_files:
                return files
    return files


def git(root, *args):
    try:
        r = subprocess.run(['git', '-C', root, *args],
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ''
    except Exception:
        return ''


def main():
    _utf8_stdio()
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
    days = 3
    if '--days' in sys.argv:
        days = int(sys.argv[sys.argv.index('--days') + 1])
    quiet = '--quiet' in sys.argv
    as_json = '--json' in sys.argv
    now = time.time()

    files = walk(root)
    sources = [(p, s, m) for p, s, m in files
               if os.path.splitext(p)[1].lower() in SRC_EXT]
    total = sum(s for _, s, _ in files)

    doc = None
    for p, s, m in files:
        if os.path.basename(p).upper().startswith('PROGRESS'):
            doc = (p, s, m)
            break

    dirty = git(root, 'status', '--porcelain')
    dirty_n = len(dirty.splitlines()) if dirty else 0
    branch = git(root, 'rev-parse', '--abbrev-ref', 'HEAD')

    def ago(sec):
        if sec < 3600:
            return f'{int(sec / 60)}m ago'
        if sec < 86400:
            return f'{sec / 3600:.1f}h ago'
        return f'{sec / 86400:.0f}d ago'

    out = [f'# DOCTOR {root}']
    scale = 'small' if len(sources) < 20 else ('medium' if len(sources) < 150 else 'large')
    out.append(f'scale   {len(files)} files · {len(sources)} source files · {human(total)} · {scale}')

    code = 0
    n_lines = 0
    if not doc:
        out.append('doc     no PROGRESS.md')
        if len(sources) < 15:
            verdict = '✅ small enough — no doc needed, reading the README is fine'
        else:
            verdict = '⛔ no handoff doc — the next window starts from zero'
            code = 2
        age_d = None
    else:
        p, s, m = doc
        age = now - m
        age_d = age / 86400
        with open(p, encoding='utf-8', errors='ignore') as fh:
            n_lines = fh.read().count('\n') + 1
        out.append(f'doc     {os.path.relpath(p, root)} · {n_lines} lines · {ago(age)}')

        # 2-second tolerance: a doc written just now is not drift
        drift = [q for q, _, mm in sources if mm > m + 2]
        note = f'{len(drift)} source files changed'
        if dirty_n:
            note += f' · {dirty_n} uncommitted in git'
        out.append(f'drift   after the doc: {note}')

        if len(drift) > 20 or (age_d > 7 and len(drift) > 5):
            verdict = '⛔ the doc is stale — handing over now would mislead the next window'
            code = 1
        elif n_lines > 120:
            verdict = f'🟡 the doc is {n_lines} lines; over 120 means it was not distilled'
            code = 1
        elif len(drift) > 3 or (dirty_n >= 5 and age > 3600):
            verdict = '🟡 some drift — rewrite the progress table and next steps before handing off'
            code = 1
        else:
            verdict = '✅ the doc is fresh — safe to hand off as-is'

    out.append(f'verdict {verdict}')

    actions = []
    if code == 2:
        actions.append('run scan.py and write a PROGRESS.md (~2 min), then open a new window')
    elif code == 1:
        actions.append('rewrite only the status line, progress table and next steps; add no sections')
    if branch:
        actions.append(f'put the branch name in the doc: {branch}')
    if actions and not quiet:
        out.append('')
        out.append('suggestions')
        for i, a in enumerate(actions, 1):
            out.append(f'  {i}. {a}')

    if not quiet and not as_json:
        out.append('')
        out.append('window hygiene (check the current chat)')
        out.append('  compact    same background explained twice / an answer pasting 3+ whole files / context half gone, >3 steps left')
        out.append('  new window the task switched modules / a delivery just landed / you start with "as I said earlier"')
        out.append('  do not push on  when context fills up the model quietly drops details and the code stops matching')

    if as_json:
        print(json.dumps({
            'root': root, 'files': len(files), 'sources': len(sources),
            'doc': os.path.relpath(doc[0], root) if doc else None,
            'doc_lines': n_lines,
            'verdict': verdict, 'code': code,
        }, ensure_ascii=False))
    else:
        print('\n'.join(out))
    sys.exit(code)


if __name__ == '__main__':
    main()
