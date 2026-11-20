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

# 标题：中英都认，顺序固定
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

SECRET_PATTERNS = [
    (re.compile(r'\bsk-[A-Za-z0-9_-]{16,}'), 'OpenAI 风格密钥'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'AWS access key'),
    (re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}'), 'GitHub token'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), '私钥'),
    (re.compile(r'\b[0-9a-f]{32,}\b'), '长十六进制串（可能是密钥）'),
    (re.compile(r'\b(?:password|passwd|secret|token)\s*[:=]\s*\S{8,}', re.I), '明文口令'),
]
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[A-Za-z]{2,}')
EMAIL_OK = ('example.com', 'example.org', 'users.noreply.github.com', 'localhost')
HOME = re.compile(r'/(?:Users|home)/[A-Za-z0-9._-]+')


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


def lint_text(text):
    lines = text.splitlines()
    problems = []   # (line, level, message)
    add = lambda n, lvl, msg: problems.append((n, lvl, msg))

    if len(lines) > MAX_LINES:
        add(0, 'error', f'{len(lines)} 行，超过 {MAX_LINES} 行（没提炼）')

    # 小节顺序
    seen = []
    for i, line in enumerate(lines, 1):
        if line.startswith('## '):
            key = section_key(line[3:])
            if key and key not in ('optional',) and key not in seen:
                seen.append(key)
    missing = [k for k, _ in SECTIONS if k not in seen]
    if missing:
        add(0, 'error', '缺少小节：' + '、'.join(missing))
    elif seen != [k for k, _ in SECTIONS]:
        add(0, 'error', '小节顺序不对：' + ' → '.join(seen))

    # 状态行日期
    head = '\n'.join(lines[:4])
    if not re.search(r'20\d\d-\d\d-\d\d', head):
        add(1, 'error', '状态行没有绝对日期（YYYY-MM-DD）')

    # 模糊表述
    for i, line in enumerate(lines, 1):
        low = line.lower()
        for word in VAGUE:
            if word.lower() in low:
                add(i, 'error', f'模糊表述「{word}」，写具体数字或状态')
                break

    # 进度表状态符号
    in_progress = False
    for i, line in enumerate(lines, 1):
        if line.startswith('## '):
            in_progress = section_key(line[3:]) == 'progress'
            continue
        if in_progress and line.startswith('|') and line.count('|') >= 4:
            cells = [c.strip() for c in line.strip('|').split('|')]
            if not cells or set(cells[0]) <= set('-: '):
                continue
            if cells[-1].lower() in ('状态', 'state', 'status', ''):
                continue          # 表头
            if any(s in cells[-1] for s in STATES):
                continue
            if re.search(r'完成|进行|待做|阻塞|done|wip|todo|block', cells[-1], re.I):
                continue
            add(i, 'error', '进度表状态不是 ✅ / 🟡 / ⬜ / ⛔')

    # 下一步
    items, in_next = [], False
    for i, line in enumerate(lines, 1):
        if line.startswith('## '):
            in_next = section_key(line[3:]) == 'next'
            continue
        if in_next and re.match(r'\s*\d+[.、)]\s+', line):
            items.append((i, re.sub(r'\s*\d+[.、)]\s+', '', line).strip()))
    if not items:
        add(0, 'error', '「下一步」里没有编号条目')
    if len(items) > MAX_NEXT:
        add(items[MAX_NEXT][0], 'error', f'下一步 {len(items)} 条，超过 {MAX_NEXT} 条')
    for n, item in items:
        if not actionable(item):
            add(n, 'error', f'下一步不可执行（没有路径、数字或动词）：{item[:28]}')

    # 密钥 / 邮箱 / 本机路径
    for i, line in enumerate(lines, 1):
        for pat, name in SECRET_PATTERNS:
            if pat.search(line):
                add(i, 'error', f'疑似{name}，删掉再交接')
        for m in EMAIL.finditer(line):
            if not m.group(0).lower().endswith(EMAIL_OK):
                add(i, 'error', f'疑似真实邮箱：{m.group(0)}')
        if HOME.search(line):
            add(i, 'warning', '含本机绝对路径，交接时别人打不开')

    # 遗留标记
    for i, line in enumerate(lines, 1):
        if re.search(r'\b(TODO|FIXME|XXX)\s*[:：]', line):
            add(i, 'error', '文档里还留着 TODO/FIXME')

    return problems, len(lines)


def main():
    _utf8_stdio()
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    as_json = '--json' in sys.argv
    strict = '--strict' in sys.argv
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
            print(f'找不到 {path}')
        sys.exit(2)

    text = open(path, encoding='utf-8', errors='ignore').read()
    problems, n_lines = lint_text(text)
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
        print(f'{path}  ({n_lines} 行)')
        for n, lvl, msg in sorted(problems):
            mark = '✗' if lvl == 'error' else '⚠'
            where = f'line {n:>3}' if n else '     '
            print(f'  {where}  {mark}  {msg}')
        if ok:
            print('  ✓ 可以交接')
        else:
            print(f'  {len(errors)} 个问题'
                  + (f'，{len(warns)} 个提醒' if warns else ''))

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
