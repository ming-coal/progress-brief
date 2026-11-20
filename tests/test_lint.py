"""lint.py: the handoff rules, made executable."""

import json
import os
import sys
import unittest

from _util import SCRIPTS, ProjectCase, run

sys.path.insert(0, SCRIPTS)
import lint  # noqa: E402

GOOD = """# Demo

> 状态：**解析写完，导出空着** · 更新 2026-11-20

## 一句话
把发票转成表格的小工具。

## 成品 / 产出
| 文件 | 规格 | 说明 |
|---|---|---|
| `lib/invoice.ts` | 40 列 | 结构定了 |

## 进度表
| # | 事项 | 位置 | 状态 |
|---|---|---|---|
| 1 | 列结构 | `lib/` | ✅ 完成 |
| 2 | 导出 | 未开始 | ⬜ 待做 |

## 文件在哪
- 代码：`src/`

## 关键决策
| 事 | 结论 | 为什么 |
|---|---|---|
| 后端 | Supabase | 不想运维 |

## 踩过的坑
1. node_modules 差点进仓库 → 加了 .gitignore

## 下一步
1. 补 `src/mod3.ts` 的错误处理
2. 写解析测试
"""


class LintUnit(unittest.TestCase):
    def test_good_doc_is_clean(self):
        problems, lines = lint.lint_text(GOOD)
        self.assertEqual([p for p in problems if p[1] == 'error'], [])
        self.assertGreater(lines, 10)

    def test_vague_words(self):
        problems, _ = lint.lint_text(GOOD.replace('导出空着', '基本完成'))
        self.assertTrue(any('模糊表述' in m for _, _, m in problems))

    def test_missing_section(self):
        problems, _ = lint.lint_text(GOOD.replace('## 关键决策', '## 别的'))
        self.assertTrue(any('缺少小节' in m for _, _, m in problems))

    def test_wrong_section_order(self):
        swapped = GOOD.replace('## 成品 / 产出', '## TEMP').replace(
            '## 关键决策', '## 成品 / 产出').replace('## TEMP', '## 关键决策')
        problems, _ = lint.lint_text(swapped)
        self.assertTrue(any('顺序不对' in m for _, _, m in problems))

    def test_needs_absolute_date(self):
        problems, _ = lint.lint_text(GOOD.replace('2026-11-20', '今天'))
        self.assertTrue(any('绝对日期' in m for _, _, m in problems))

    def test_overlong(self):
        problems, _ = lint.lint_text(GOOD + '填充\n' * 120)
        self.assertTrue(any('超过 120 行' in m for _, _, m in problems))

    def test_next_step_must_be_actionable(self):
        problems, _ = lint.lint_text(GOOD.replace('2. 写解析测试', '2. 继续完善'))
        self.assertTrue(any('不可执行' in m for _, _, m in problems))

    def test_next_steps_capped(self):
        extra = GOOD + ''.join(f'{i}. 改 `a{i}.ts` 的错\n' for i in range(3, 9))
        problems, _ = lint.lint_text(extra)
        self.assertTrue(any('超过 5 条' in m for _, _, m in problems))

    def test_bad_state_marker(self):
        problems, _ = lint.lint_text(GOOD.replace('⬜ 待做', '差不多了'))
        self.assertTrue(any('状态不是' in m for _, _, m in problems))

    def test_secrets_are_errors(self):
        fake = ['sk-' + 'a' * 24, 'gh' + 'p_' + 'b' * 30, 'pass' + 'word: hunter2hunter2']
        for secret in fake:
            problems, _ = lint.lint_text(GOOD + f'\n{secret}\n')
            self.assertTrue(any('删掉再交接' in m for _, lv, m in problems if lv == 'error'),
                            secret)

    def test_real_email_blocked_but_example_allowed(self):
        bad, _ = lint.lint_text(GOOD + '\ntest@realcompany.com\n')
        self.assertTrue(any('邮箱' in m for _, _, m in bad))
        ok, _ = lint.lint_text(GOOD + '\ntest@example.com\n')
        self.assertFalse(any('邮箱' in m for _, _, m in ok))

    def test_home_path_is_only_a_warning(self):
        problems, _ = lint.lint_text(GOOD + '\n见 /Users/someone/proj\n')
        self.assertTrue(any(lv == 'warning' for _, lv, _ in problems))
        self.assertFalse(any(lv == 'error' for _, lv, _ in problems))


class LintCli(ProjectCase):
    def test_clean_doc_exits_0(self):
        self.write('PROGRESS.md', GOOD)
        self.assertEqual(run('lint.py', self.root).returncode, 0)

    def test_missing_doc_exits_2(self):
        self.assertEqual(run('lint.py', self.root).returncode, 2)

    def test_bad_doc_exits_1(self):
        self.write('PROGRESS.md', GOOD.replace('2. 写解析测试', '2. 继续完善'))
        self.assertEqual(run('lint.py', self.root).returncode, 1)

    def test_json_mode(self):
        self.write('PROGRESS.md', GOOD)
        data = json.loads(run('lint.py', self.root, '--json').stdout)
        self.assertTrue(data['ok'])
        self.assertEqual(data['errors'], 0)
        self.assertIn('lines', data)

    def test_rules_can_be_listed(self):
        out = run('lint.py', '--rules')
        self.assertEqual(out.returncode, 0)
        for needle in ('length', 'sections', 'email', 'secrets', 'paths'):
            self.assertIn(needle, out.stdout)

    def test_example_email_is_allowed_by_design(self):
        self.write('PROGRESS.md', GOOD + '\ncontact demo@example.com\n')
        out = run('lint.py', self.root)
        self.assertEqual(out.returncode, 0)

    def test_strict_turns_warnings_into_failure(self):
        self.write('PROGRESS.md', GOOD + '\n见 /Users/someone/proj\n')
        self.assertEqual(run('lint.py', self.root).returncode, 0)
        self.assertEqual(run('lint.py', self.root, '--strict').returncode, 1)


if __name__ == '__main__':
    unittest.main()
