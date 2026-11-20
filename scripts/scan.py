#!/usr/bin/env python3
"""Compact project scanner for progress docs.

Prints a ~60 line inventory plus a token ledger, so an agent can write or
update a PROGRESS.md without reading the whole tree.

Usage:
  python3 scan.py [path] [--days 7] [--json] [--no-ledger]
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
from pathlib import Path

SKIP = {
    'node_modules', '.git', '.next', 'dist', 'build', 'out', '.cache',
    '__pycache__', '.venv', 'venv', '.DS_Store', 'vendor', 'target',
    '.turbo', 'coverage', '.idea', '.vscode', '.netlify', '.open-next',
    '.svelte-kit', '.parcel-cache', '.pytest_cache', '.mypy_cache',
}
TEXT_EXT = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.json', '.md',
    '.mdx', '.txt', '.yml', '.yaml', '.toml', '.css', '.scss', '.html',
    '.vue', '.svelte', '.go', '.rs', '.java', '.kt', '.rb', '.php', '.sh',
    '.sql', '.swift', '.c', '.h', '.cpp', '.cs', '.lua', '.ex', '.exs',
    '.graphql', '.astro', '.lock',
}
BULK_EXT = {'.map', '.lock', '.tsbuildinfo', '.min.js', '.min.css'}
BULK_NAME = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lockb',
    'tsconfig.tsbuildinfo', 'Cargo.lock', 'poetry.lock', 'go.sum',
}
DOC_NAME = ('readme', 'agents.md', 'claude.md', 'contributing.md')
HUMAN = [[1 << 30, 'GB'], [1 << 20, 'MB'], [1 << 10, 'KB']]
# The table text we generate (paths + numbers + indentation) costs about 38%
# more than prose of the same length. The factor applies only to the brief
# itself and is skipped when tiktoken is available.
BRIEF_TEXT_FACTOR = 1.38

LEDGER = Path(os.environ.get('PROGRESS_BRIEF_LEDGER')
               or Path(__file__).resolve().parent.parent / '.usage.jsonl')


def human(n):
    for unit, name in HUMAN:
        if n >= unit:
            return f'{n / unit:.1f}{name}'
    return f'{n}B'


def tok(n):
    return f'{n / 1000:.0f}k' if n >= 1000 else str(int(n))


def walk(root, max_files=20000):
    files = []
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.git')]
        for n in names:
            if n in ('node_modules', '.DS_Store'):
                continue
            p = os.path.join(base, n)
            try:
                st = os.stat(p)
            except OSError:
                continue
            files.append((p, st.st_size, st.st_mtime))
            if len(files) >= max_files:
                return files
    return files


def text_key(p):
    name = os.path.basename(p).lower()
    if name in BULK_NAME or name.endswith('.min.js') or name.endswith('.min.css'):
        return ''
    ext = os.path.splitext(name)[1]
    return ext if ext in TEXT_EXT else ''


def is_source(p):
    """Text files a pickup would plausibly open (no docs, no bulk)."""
    ext = text_key(p)
    return bool(ext) and ext not in ('.md', '.mdx', '.txt')


def is_doc(p):
    name = os.path.basename(p).lower()
    if name.startswith('progress'):
        return False
    return text_key(p) in ('.md', '.mdx', '.txt') or name in DOC_NAME


def est_tokens(text):
    """Token estimate: 1.6876 per CJK char, 0.2510 per other char.

    Constants fitted with scripts/calibrate.py against tiktoken/cl100k on a
    263-file corpus (mixed code, English and Chinese docs): median error 6.6%.
    """
    cjk = 0
    for ch in text:
        if '\u3400' <= ch <= '\u9fff' or '\uf900' <= ch <= '\ufaff':
            cjk += 1
    return cjk * 1.6876 + (len(text) - cjk) * 0.2510


_COUNTER = None


def counter():
    """Return (fn, label). Uses tiktoken if available, else the heuristic.

    Force either side with PROGRESS_BRIEF_TOKENIZER=heuristic|tiktoken.
    """
    global _COUNTER
    if _COUNTER is not None:
        return _COUNTER
    want = os.environ.get('PROGRESS_BRIEF_TOKENIZER', '').lower()
    if want != 'heuristic':
        try:
            import tiktoken
            enc = tiktoken.get_encoding('cl100k_base')
            _COUNTER = (lambda s: len(enc.encode(s)), 'tiktoken')
            return _COUNTER
        except Exception:
            pass
    _COUNTER = (est_tokens, 'heuristic')
    return _COUNTER


def tokens_per_byte(paths):
    """Tokens/byte from an even sample of the repo's text."""
    if not paths:
        return 0.26
    count, _ = counter()
    step = max(1, len(paths) // 40)
    sample = paths[::step][:40]
    tb = tt = 0
    for p in sample:
        try:
            raw = open(p, 'rb').read(400_000)
        except OSError:
            continue
        tb += len(raw)
        tt += count(raw.decode('utf-8', 'ignore'))
        if tb > 1_500_000:
            break
    return (tt / tb) if tb else 0.26


def git(root, *args):
    try:
        out = subprocess.run(
            ['git', '-C', root, *args],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else ''
    except Exception:
        return ''


def read_ledger():
    rows = []
    if not LEDGER.exists():
        return rows
    for line in LEDGER.read_text(encoding='utf-8', errors='ignore').splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def main():
    _utf8_stdio()
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
    days = 7
    if '--days' in sys.argv:
        days = int(sys.argv[sys.argv.index('--days') + 1])
    as_json = '--json' in sys.argv
    no_ledger = '--no-ledger' in sys.argv

    files = walk(root)
    now = time.time()
    total = sum(s for _, s, _ in files)

    lines = []
    add = lines.append
    add(f'# SCAN {root}')
    add(f'files: {len(files)}  size: {human(total)}')

    # top-level directories
    per_dir = {}
    for p, s, _ in files:
        rel = os.path.relpath(p, root)
        top = rel.split(os.sep)[0] if os.sep in rel else '(root files)'
        d = per_dir.setdefault(top, [0, 0])
        d[0] += 1
        d[1] += s
    add('')
    add('## top level')
    for name, (n, s) in sorted(per_dir.items(), key=lambda kv: -kv[1][1])[:12]:
        add(f'  {name:<28} {n:>5} files  {human(s)}')

    # recent changes
    add('')
    add(f'## changed in {days}d')
    recent = sorted(files, key=lambda f: -f[2])[:12]
    for p, s, m in recent:
        if now - m > days * 86400:
            continue
        stamp = time.strftime('%m-%d %H:%M', time.localtime(m))
        add(f'  {stamp}  {human(s):>7}  {os.path.relpath(p, root)}')

    # progress docs
    add('')
    add('## progress docs')
    found = False
    for p, s, m in files:
        base = os.path.basename(p)
        if base.upper().startswith('PROGRESS') or base in ('STATUS.md', 'HANDOFF.md'):
            found = True
            with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                n_lines = fh.read().count('\n') + 1
            age = int((now - m) / 86400)
            add(f'  {os.path.relpath(p, root)}  ({n_lines} lines, {age}d old)')
    if not found:
        add('  (none)')

    # TODO count
    todos = []
    for p, _, _ in files:
        if not text_key(p) or os.path.getsize(p) > 400_000:
            continue
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                txt = fh.read()
        except OSError:
            continue
        n = txt.count('TODO') + txt.count('FIXME')
        if n:
            todos.append((n, os.path.relpath(p, root)))
    add('')
    add('## todos')
    if todos:
        for n, p in sorted(todos, reverse=True)[:6]:
            add(f'  {n:>2}  {p}')
    else:
        add('  (none)')

    # git
    dirty_n = 0
    if os.path.isdir(os.path.join(root, '.git')):
        branch = git(root, 'rev-parse', '--abbrev-ref', 'HEAD')
        dirty = git(root, 'status', '--porcelain')
        dirty_n = len(dirty.splitlines())
        add('')
        add(f'## git  branch {branch or "-"}  dirty {dirty_n} files')
        for line in git(root, 'log', '-5', '--pretty=%h %ad %s', '--date=short').splitlines():
            add('  ' + line)

    # package.json scripts
    pkg = os.path.join(root, 'package.json')
    if os.path.exists(pkg):
        try:
            data = json.load(open(pkg, encoding='utf-8'))
            scripts = data.get('scripts', {})
            add('')
            add('## scripts')
            for k, v in list(scripts.items())[:10]:
                add(f'  {k}: {v}')
        except Exception:
            pass

    # ---- token ledger ----
    texts = [p for p, _, _ in files if text_key(p)]
    srcs = [p for p in texts if is_source(p)]
    docs = [p for p in texts if is_doc(p)]
    ratios = tokens_per_byte(texts + docs)
    size_of = {p: s for p, s, _ in files}

    worst = sum(size_of[p] for p in texts) * ratios
    typical_set = [p for p in docs if os.path.dirname(p) == root] \
        + sorted(srcs, key=lambda p: -size_of.get(p, 0))[:20]
    typical = sum(size_of[p] for p in set(typical_set)) * ratios

    count, backend = counter()
    brief_lines = count('\n'.join(lines))
    if backend != 'tiktoken':
        brief_lines *= BRIEF_TEXT_FACTOR
    brief_lines += 150                              # the ledger block itself
    progress_tok = 0.0
    for p, s, _ in files:
        if os.path.basename(p).upper().startswith('PROGRESS'):
            try:
                progress_tok += count(open(p, encoding='utf-8', errors='ignore').read())
            except OSError:
                pass
    brief = brief_lines + progress_tok

    if len(texts) < 15:
        add('')
        add(f'## note  only {len(texts)} text files — reading the README is cheaper, skip PROGRESS.md')

    add('')
    label = 'exact' if backend == 'tiktoken' else 'estimated, ±20%'
    add(f'## token ledger ({label})')
    add(f'  worst    every text file      {len(texts):>4} files  ~ {tok(worst)} tok')
    add(f'  typical  root docs + 20 src   {len(set(typical_set)):>4} files  ~ {tok(typical)} tok')
    add(f'  brief    scan output + PROGRESS.md             ~ {tok(brief)} tok')
    if typical > 0 and brief >= typical:
        add(f'  -> project too small: writing the doc costs more than reading it'
            f' (+{tok(brief - typical)} tok), you can skip it')
    elif typical > 0:
        gain = 100 * (1 - brief / typical)
        tail = '  ·  small project, modest gain' if gain < 30 else ''
        add(f'  -> {gain:.0f}% cheaper than typical'
            f'  ·  {100 * (1 - brief / worst):.0f}% cheaper than worst case{tail}')

    if not as_json and not no_ledger:
        rows = read_ledger()
        try:
            LEDGER.parent.mkdir(parents=True, exist_ok=True)
            with open(LEDGER, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps({
                    'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'root': root, 'files': len(texts),
                    'worst': round(worst), 'typical': round(typical),
                    'brief': round(brief),
                }) + '\n')
        except OSError:
            pass
        if rows:
            saved = sum(max(0, r.get('typical', 0) - r.get('brief', 0)) for r in rows)
            saved += max(0, typical - brief)
            if saved < 100:
                add(f'  {len(rows) + 1} runs so far  ·  nothing saved on these projects yet')
            else:
                add(f'  {len(rows) + 1} runs so far  ~ {tok(saved)} tok saved')

    if as_json:
        print(json.dumps({
            'root': root, 'files': len(files), 'bytes': total,
            'text_files': len(texts), 'dirty': dirty_n,
            'tokens': {'worst': round(worst), 'typical': round(typical),
                       'brief': round(brief)},
        }, ensure_ascii=False))
        return

    print('\n'.join(lines))


if __name__ == '__main__':
    main()
