#!/usr/bin/env python3
"""Handoff / context-hygiene advisor.

Answers one question: 现在该继续、该更新文档、还是该开新窗口？

  python3 doctor.py [path] [--days 3]

退出码：0 健康 / 1 需要更新文档 / 2 没有文档
"""

import json
import os
import subprocess
import sys
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
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ''
    except Exception:
        return ''


def main():
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
            return f'{int(sec / 60)} 分钟前'
        if sec < 86400:
            return f'{sec / 3600:.1f} 小时前'
        return f'{sec / 86400:.0f} 天前'

    out = [f'# DOCTOR {root}']
    scale = '小型' if len(sources) < 20 else ('中型' if len(sources) < 150 else '大型')
    out.append(f'规模    {len(files)} 文件 · {len(sources)} 个源文件 · {human(total)} · {scale}')

    code = 0
    n_lines = 0
    if not doc:
        out.append('文档    没有 PROGRESS.md')
        if len(sources) < 15:
            verdict = '✅ 规模够小，不需要文档，直接读 README 也行'
        else:
            verdict = '⛔ 没有交接文档，下一个窗口要从零读代码'
            code = 2
        age_d = None
    else:
        p, s, m = doc
        age = now - m
        age_d = age / 86400
        with open(p, errors='ignore') as fh:
            n_lines = fh.read().count('\n') + 1
        out.append(f'文档    {os.path.relpath(p, root)} · {n_lines} 行 · {ago(age)}')

        # 2 秒容差：刚写完文档时不算漂移
        drift = [q for q, _, mm in sources if mm > m + 2]
        note = f'{len(drift)} 个源文件改动'
        if dirty_n:
            note += f' · git 未提交 {dirty_n}'
        out.append(f'漂移    文档后 {note}')

        if len(drift) > 20 or (age_d > 7 and len(drift) > 5):
            verdict = '⛔ 文档已过期，现在交接会误导下一个窗口'
            code = 1
        elif n_lines > 120:
            verdict = f'🟡 文档 {n_lines} 行，超过 120 行说明没提炼，先砍再交接'
            code = 1
        elif len(drift) > 3 or (dirty_n >= 5 and age > 3600):
            verdict = '🟡 有漂移，交接前更新「进度表 / 下一步」两节就够'
            code = 1
        else:
            verdict = '✅ 文档新鲜，可以直接开新窗口交接'

    out.append(f'判断    {verdict}')

    actions = []
    if code == 2:
        actions.append('跑 scan.py 写一份 PROGRESS.md（约 2 分钟），再开新窗口')
    elif code == 1:
        actions.append('只改 PROGRESS.md 的状态行、进度表、下一步；别追加新章节')
    if branch:
        actions.append(f'交接时把分支名写进文档：{branch}')
    if actions and not quiet:
        out.append('')
        out.append('建议')
        for i, a in enumerate(actions, 1):
            out.append(f'  {i}. {a}')

    if not quiet and not as_json:
        out.append('')
        out.append('窗口卫生（当前对话自检）')
        out.append('  该压缩  同一话题第 2 次解释背景 / 一次回答要贴 3 个以上文件全文 / 上下文过半但还剩 >3 步')
        out.append('  该新开  任务换模块 / 一次交付或合并完成 / 开始用「我记得前面说过」推进')
        out.append('  别硬撑  上下文满了还继续，模型会悄悄丢细节，写出来的东西对不上代码')

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
