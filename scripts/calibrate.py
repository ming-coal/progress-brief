#!/usr/bin/env python3
"""Calibrate the token heuristic against a real tokenizer.

Only useful when `tiktoken` is installed; it is a development tool.

  python3 scripts/calibrate.py <dir> [<dir> ...]
  python3 scripts/calibrate.py --fit <dir>      # 最小二乘拟合 a、b

The heuristic counts  t = a*cjk + b*other  and the scanner applies it to a
sampled bytes-per-token ratio, so this prints both the fitted constants and
the per-file error once those constants are applied.
"""

import os
import sys

def _utf8_stdio():
    """Windows consoles default to cp1252; our output is UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass



sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan  # noqa: E402


def corpus(roots, max_files=400, max_bytes=200_000):
    for root in roots:
        for p, size, _ in scan.walk(root):
            if not scan.text_key(p) or size > max_bytes or size == 0:
                continue
            try:
                raw = open(p, 'rb').read()
            except OSError:
                continue
            text = raw.decode('utf-8', 'ignore')
            if not text.strip():
                continue
            yield p, text
            max_files -= 1
            if max_files <= 0:
                return


def parts(text):
    cjk = sum(1 for ch in text
              if '\u3400' <= ch <= '\u9fff' or '\uf900' <= ch <= '\ufaff')
    return cjk, len(text) - cjk


def fit(rows):
    """Least squares for t = a*c + b*o through the origin."""
    scc = sum(c * c for c, _, _ in rows)
    soo = sum(o * o for _, o, _ in rows)
    sco = sum(c * o for c, o, _ in rows)
    sct = sum(c * t for c, _, t in rows)
    sot = sum(o * t for _, o, t in rows)
    det = scc * soo - sco * sco
    if abs(det) < 1e-9:
        return 1 / 1.5, 1 / 3.6
    a = (sct * soo - sot * sco) / det
    b = (sot * scc - sct * sco) / det
    return a, b


def main():
    _utf8_stdio()
    try:
        import tiktoken
    except ImportError:
        sys.exit('需要 tiktoken：pip install tiktoken')
    enc = tiktoken.get_encoding('cl100k_base')

    args = [a for a in sys.argv[1:] if not a.startswith('-')] or ['.']
    do_fit = '--fit' in sys.argv

    rows, errs = [], []
    for p, text in corpus(args):
        c, o = parts(text)
        true = len(enc.encode(text, disallowed_special=()))
        rows.append((c, o, true))
        heur = scan.est_tokens(text)
        if true:
            errs.append(abs(heur - true) / true)

    if not rows:
        sys.exit('没有可校准的文本文件')

    errs.sort()
    n = len(errs)
    print(f'files           {n}')
    print(f'中位误差        {errs[n // 2] * 100:.1f}%')
    print(f'p90 误差        {errs[int(n * 0.9)] * 100:.1f}%')
    print(f'平均绝对误差    {sum(errs) / n * 100:.1f}%')

    if do_fit:
        a, b = fit(rows)
        print(f'\n拟合常数        a(cjk)={a:.4f}  b(ascii)={b:.4f}')
        print(f'等价于          {1 / a:.2f} 字符/token（中文）  {1 / b:.2f} 字符/token（其余）')
        fitted = [(abs(a * c + b * o - t) / t) for c, o, t in rows if t]
        fitted.sort()
        print(f'拟合后中位误差  {fitted[len(fitted) // 2] * 100:.1f}%')
        print(f'拟合后 p90      {fitted[int(len(fitted) * 0.9)] * 100:.1f}%')


if __name__ == '__main__':
    main()
