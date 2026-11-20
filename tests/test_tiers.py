"""Reproduce the three-tier table from the README, in CI.

tiny   -> the tool refuses
small  -> modest saving
large  -> large saving
"""

import os
import re
import unittest

from _util import ProjectCase

LANDING = """# {name}

> 状态：**进行中** · 更新 2026-11-20

## 一句话
测试用项目。

## 成品 / 产出
| 文件 | 规格 | 说明 |
|---|---|---|

## 进度表
| # | 事项 | 位置 | 状态 |
|---|---|---|---|
| 1 | 骨架 | `src/` | ✅ 完成 |

## 文件在哪
- 代码：`src/`

## 关键决策
| 事 | 结论 | 为什么 |
|---|---|---|
| 语言 | Python | 快 |

## 踩过的坑
1. 无

## 下一步
1. 补 `src/a.py` 的错误处理
"""


def saving(stdout):
    """Pull the percentage out of the ledger line."""
    line = [l for l in stdout.splitlines() if l.strip().startswith('→')]
    if not line:
        return None
    m = re.search(r'比典型省\s*(-?\d+)%', line[0])
    return int(m.group(1)) if m else None


class Tiers(ProjectCase):
    def build(self, n_src, n_docs=1, body=12):
        for i in range(n_src):
            self.write(f'src/mod{i}.py',
                       f'# module {i}\n' + 'def f(x):\n    return x + 1\n' * body)
        for i in range(n_docs):
            self.write(f'docs/note{i}.md', '# note\n' + 'a paragraph of prose. ' * 40)

    def test_tiny_refuses(self):
        self.write('README.md', '# hi\n')
        self.write('a.py', 'print(1)\n')
        out = self.scan().stdout
        self.assertIn('这个项目太小', out)
        self.assertIsNone(saving(out))

    def test_small_is_modest(self):
        self.build(28)
        self.write('PROGRESS.md', LANDING.format(name='small'))
        out = self.scan().stdout
        self.assertIsNotNone(saving(out))
        self.assertLess(saving(out), 70)

    def test_large_is_big(self):
        self.build(180, n_docs=8, body=90)
        self.write('PROGRESS.md', LANDING.format(name='large'))
        out = self.scan().stdout
        self.assertGreaterEqual(saving(out), 85)


if __name__ == '__main__':
    unittest.main()
