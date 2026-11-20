#!/usr/bin/env python3
"""Lint a PROGRESS.md against the handoff rules.

The rules lived in a prompt before, which meant they were optional. This makes
them executable: 0 = clean, 1 = problems, 2 = no document.

  python3 lint.py [path-to-PROGRESS.md or project dir] [--json] [--strict]
"""

import json
import os
import re
import sys
from urllib.parse import unquote


def _utf8_stdio():
    """Windows consoles default to cp1252; our output is UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


MAX_LINES = 120
MAX_NEXT = 5
STATES = ('✅', '🟡', '⬜', '⛔')

# --- bilingual vocabulary (data, not prose) --------------------------------
# The only non-ASCII in this file. It is what lets the linter read a Chinese
# document and an English one with the same code. tests/test_no_cjk.py allows
# Chinese here and nowhere else, comments included.

# Headings: both languages, order fixed.
SECTIONS = [
    ('one_liner', ('一句话', 'one-liner', 'one liner', 'summary')),
    ('output', ('成品', '产出', 'output', 'deliverables')),
    ('progress', ('进度表', '进度', 'progress', 'status table')),
    ('where', ('文件在哪', '文件位置', 'where things live', 'layout', 'where')),
    ('decisions', ('关键决策', '决策', 'decisions', 'decision log')),
    ('pitfalls', ('踩过的坑', '坑', 'pitfalls', 'gotchas', 'lessons')),
    ('next', ('下一步', 'next steps', 'next', 'todo')),
]
OPTIONAL = ('待确认', 'open questions', 'questions')

VAGUE = (
    '基本完成', '持续优化', '差不多', '继续完善', '大体完成', '大致完成',
    '进一步完善', '不断优化', 'basically done', 'almost done',
    'keep improving', 'continuously improving', 'polish further',
)

VERBS = (
    '补', '改', '跑', '写', '接', '做', '删', '加', '测', '发', '查', '换', '修',
    '拆', '合', '导', '传', '审', '确认', '定', '录', '剪', '配', '上线', '迁移',
    'fix', 'run', 'write', 'add', 'test', 'ship', 'review', 'remove', 'rename',
    'deploy', 'check', 'migrate', 'record', 'update', 'merge', 'verify',
    'wire', 'persist', 'build', 'split', 'refactor', 'polish', 'instrument',
)

HEADER_CELLS = ('状态', 'state', 'status', '')
STATE_SYNONYMS = re.compile(r'完成|进行|待做|阻塞|done|wip|todo|block', re.I)
# "1." and "1、" both start a numbered item; the full-width colon ends TODO:
NUMBERED = re.compile(r'\s*\d+[.、)]\s+')
TODO_MARK = re.compile(r'\b(TODO|FIXME|XXX)\s*[:：]')
# --- end bilingual vocabulary ----------------------------------------------

SECRET_PATTERNS = [
    (re.compile(r'\bsk-[A-Za-z0-9_-]{16,}'), 'OpenAI-style key'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'AWS access key'),
    (re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}'), 'GitHub token'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'private key'),
    (re.compile(r'\b[0-9a-f]{32,}\b'), 'long hex string (possibly a key)'),
    (re.compile(r'\b(?:password|passwd|secret|token)\s*[:=]\s*\S{8,}', re.I), 'plaintext password'),
]
RULES = [
    ('length', 'at most 120 lines'),
    ('sections', 'required sections, fixed order'),
    ('date', 'absolute date in the status line'),
    ('vague', 'vague wording: "basically done", "almost done", "keep improving" …'),
    ('states', 'progress table uses only ✅ 🟡 ⬜ ⛔'),
    ('next', 'max 5 next steps, each one actionable'),
    ('secrets', 'keys: sk- / ghp_ / AKIA / private keys / long hex / plaintext passwords'),
    ('email', 'real emails; example.com and localhost are allowed'),
    ('paths', 'local absolute paths → warning, not fatal'),
    ('links', 'images must exist (error), relative links must exist (warning)'),
    ('todo', 'leftover TODO: / FIXME:'),
]

EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[A-Za-z]{2,}')
EMAIL_OK = ('example.com', 'example.org', 'users.noreply.github.com', 'localhost')
HOME = re.compile(r'/(?:Users|home)/[A-Za-z0-9._-]+')

# ![alt](path "title") or [text](path)
LINK = re.compile(r'(!?)\[([^\]]*)\]\(\s*([^)\s]*)(?:\s+"[^"]*")?\s*\)')
REMOTE = ('http://', 'https://', '//', '#', 'mailto:', 'tel:', 'data:', 'ftp://')


def _is_remote(target):
    return target.startswith(REMOTE)


def check_links(text, root):
    """Dead relative links. Only the ones we can resolve, so nothing is guessed.

    Images are errors (they render as a broken box); plain links are warnings
    (the target may live in a sibling repo). Fenced code is skipped.
    """
    found = []
    if not root:
        return found
    base = os.path.abspath(root)
    fenced = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith('```'):
            fenced = not fenced
            continue
        if fenced:
            continue
        for m in LINK.finditer(line):
            bang, _alt, raw = m.groups()
            target = unquote(raw.strip())
            if not target or _is_remote(target):
                continue
            if any(c in target for c in '<>{}*|'):     # template placeholder, not a path
                continue
            path = target.split('#')[0].split('?')[0]
            if not path:
                continue
            full = os.path.normpath(os.path.join(base, path.lstrip('/')))
            try:
                if os.path.normcase(os.path.commonpath([base, full])) != os.path.normcase(base):
                    continue          # outside the project, not our business
            except ValueError:        # different drives on Windows
                continue
            if os.path.exists(full):
                continue
            if bang:
                found.append((i, 'error',
                              f'image not found: {path} (it renders as a broken box)'))
            else:
                found.append((i, 'warning',
                              f'relative link points at a missing file: {path}'))
    return found


def section_key(heading):
    low = heading.strip().lower()
    for key, names in SECTIONS:
        for n in names:
            if low.startswith(n.lower()) or n.lower() in low:
                return key
    for n in OPTIONAL:
        if n.lower() in low:
            return 'optional'
    return None


def actionable(item):
    if re.search(r'`[^`]+`', item):
        return True
    if re.search(r'\d', item):
        return True
    low = item.lower()
    return any(v in low for v in VERBS)


def lint_text(text, root=None):
    lines = text.splitlines()
    problems = []   # (line, level, message)
    add = lambda n, lvl, msg: problems.append((n, lvl, msg))

    if len(lines) > MAX_LINES:
        add(0, 'error', f'{len(lines)} lines, over the {MAX_LINES}-line cap (not distilled)')

    # Section order
    seen = []
    for i, line in enumerate(lines, 1):
        if line.startswith('## '):
            key = section_key(line[3:])
            if key and key not in ('optional',) and key not in seen:
                seen.append(key)
    missing = [k for k, _ in SECTIONS if k not in seen]
    if missing:
        add(0, 'error', 'missing sections: ' + ', '.join(missing))
    elif seen != [k for k, _ in SECTIONS]:
        add(0, 'error', 'sections out of order: ' + ' -> '.join(seen))

    # Absolute date in the status line
    head = '\n'.join(lines[:4])
    if not re.search(r'20\d\d-\d\d-\d\d', head):
        add(1, 'error', 'status line has no absolute date (YYYY-MM-DD)')

    # Vague wording
    for i, line in enumerate(lines, 1):
        low = line.lower()
        for word in VAGUE:
            if word.lower() in low:
                add(i, 'error', f'vague wording "{word}" — write a number or a state')
                break

    # State markers in the progress table
    in_progress = False
    for i, line in enumerate(lines, 1):
        if line.startswith('## '):
            in_progress = section_key(line[3:]) == 'progress'
            continue
        if in_progress and line.startswith('|') and line.count('|') >= 4:
            cells = [c.strip() for c in line.strip('|').split('|')]
            if not cells or set(cells[0]) <= set('-: '):
                continue
            if cells[-1].lower() in HEADER_CELLS:
                continue          # header row
            if any(s in cells[-1] for s in STATES):
                continue
            if STATE_SYNONYMS.search(cells[-1]):
                continue
            add(i, 'error', 'progress state must be one of ✅ / 🟡 / ⬜ / ⛔')

    # Next steps
    items, in_next = [], False
    for i, line in enumerate(lines, 1):
        if line.startswith('## '):
            in_next = section_key(line[3:]) == 'next'
            continue
        if in_next and NUMBERED.match(line):
            items.append((i, NUMBERED.sub('', line).strip()))
    if not items:
        add(0, 'error', 'the "next steps" section has no numbered items')
    if len(items) > MAX_NEXT:
        add(items[MAX_NEXT][0], 'error', f'{len(items)} next steps, the cap is {MAX_NEXT}')
    for n, item in items:
        if not actionable(item):
            add(n, 'error', f'next step is not actionable (no path, number or verb): {item[:28]}')

    # Keys / emails / local paths
    for i, line in enumerate(lines, 1):
        for pat, name in SECRET_PATTERNS:
            if pat.search(line):
                add(i, 'error', f'possible {name} — remove it before handing off')
        for m in EMAIL.finditer(line):
            if not m.group(0).lower().endswith(EMAIL_OK):
                add(i, 'error', f'looks like a real email: {m.group(0)}')
        if HOME.search(line):
            add(i, 'warning', 'local absolute path — the next person cannot open it')

    # Leftover markers
    for i, line in enumerate(lines, 1):
        if TODO_MARK.search(line):
            add(i, 'error', 'TODO/FIXME left in the document')

    # Dead links: a broken image you see yourself, a broken link the next
    # person walks into.
    for n, lvl, msg in check_links(text, root):
        add(n, lvl, msg)

    return problems, len(lines)


def main():
    _utf8_stdio()
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    as_json = '--json' in sys.argv
    strict = '--strict' in sys.argv

    if '--rules' in sys.argv:
        print('lint.py rules:')
        for i, (key, desc) in enumerate(RULES, 1):
            print(f'  {i:>2}. {key:<9} {desc}')
        print('\nexample.com and localhost are allowed so documents can show examples.')
        print('local absolute paths are warnings; add --strict to make them fail.')
        return
    target = args[0] if args else '.'

    if os.path.isdir(target):
        path = os.path.join(target, 'PROGRESS.md')
    else:
        path = target
    if not os.path.exists(path):
        if as_json:
            print(json.dumps({'ok': False, 'error': 'no PROGRESS.md', 'path': path},
                             ensure_ascii=False))
        else:
            print(f'no PROGRESS.md at {path}')
        sys.exit(2)

    text = open(path, encoding='utf-8', errors='ignore').read()
    problems, n_lines = lint_text(text, os.path.dirname(os.path.abspath(path)))
    errors = [p for p in problems if p[1] == 'error']
    warns = [p for p in problems if p[1] == 'warning']
    ok = not errors and (not warns or not strict)

    if as_json:
        print(json.dumps({
            'ok': ok, 'path': path, 'lines': n_lines,
            'errors': len(errors), 'warnings': len(warns),
            'problems': [{'line': n, 'level': l, 'message': m} for n, l, m in problems],
        }, ensure_ascii=False))
    else:
        print(f'{path}  ({n_lines} lines)')
        for n, lvl, msg in sorted(problems):
            mark = '✗' if lvl == 'error' else '⚠'
            where = f'line {n:>3}' if n else '     '
            print(f'  {where}  {mark}  {msg}')
        if ok:
            print('  ✓ safe to hand off')
        else:
            print(f'  {len(errors)} problem(s)'
                  + (f', {len(warns)} warning(s)' if warns else ''))

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
