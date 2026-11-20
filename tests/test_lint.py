"""lint.py: the handoff rules, made executable."""

import json
import sys
import unittest

from _util import SCRIPTS, ProjectCase, run

sys.path.insert(0, SCRIPTS)
import lint  # noqa: E402

GOOD = """# Demo

> Status: **parser done, export empty** · updated 2026-11-20

## One-liner
A tiny tool that turns invoices into tables.

## Output
| file | spec | note |
|---|---|---|
| `lib/invoice.ts` | 40 columns | the schema is settled |

## Progress
| # | item | where | state |
|---|---|---|---|
| 1 | column schema | `lib/` | ✅ done |
| 2 | export | not started | ⬜ todo |

## Where things live
- code: `src/`

## Decisions
| topic | choice | why |
|---|---|---|
| backend | Supabase | no ops |

## Pitfalls
1. node_modules almost got committed -> .gitignore

## Next steps
1. add error handling to `src/mod3.ts`
2. write parser tests
"""


class LintUnit(unittest.TestCase):
    def test_good_doc_is_clean(self):
        problems, lines = lint.lint_text(GOOD)
        self.assertEqual([p for p in problems if p[1] == 'error'], [])
        self.assertGreater(lines, 10)

    def test_vague_words(self):
        problems, _ = lint.lint_text(GOOD.replace('export empty', 'basically done'))
        self.assertTrue(any('vague wording' in m for _, _, m in problems))

    def test_missing_section(self):
        problems, _ = lint.lint_text(GOOD.replace('## Decisions', '## Misc'))
        self.assertTrue(any('missing sections' in m for _, _, m in problems))

    def test_wrong_section_order(self):
        swapped = GOOD.replace('## Output', '## TEMP').replace(
            '## Decisions', '## Output').replace('## TEMP', '## Decisions')
        problems, _ = lint.lint_text(swapped)
        self.assertTrue(any('out of order' in m for _, _, m in problems))

    def test_needs_absolute_date(self):
        problems, _ = lint.lint_text(GOOD.replace('2026-11-20', 'today'))
        self.assertTrue(any('absolute date' in m for _, _, m in problems))

    def test_overlong(self):
        problems, _ = lint.lint_text(GOOD + 'filler\n' * 120)
        self.assertTrue(any('120-line cap' in m for _, _, m in problems))

    def test_next_step_must_be_actionable(self):
        problems, _ = lint.lint_text(
            GOOD.replace('2. write parser tests', '2. better documentation'))
        self.assertTrue(any('not actionable' in m for _, _, m in problems))

    def test_next_steps_capped(self):
        extra = GOOD + ''.join(f'{i}. patch `a{i}.ts`\n' for i in range(3, 9))
        problems, _ = lint.lint_text(extra)
        self.assertTrue(any('the cap is 5' in m for _, _, m in problems))

    def test_bad_state_marker(self):
        problems, _ = lint.lint_text(GOOD.replace('⬜ todo', 'halfway there'))
        self.assertTrue(any('progress state must be' in m for _, _, m in problems))

    def test_secrets_are_errors(self):
        fake = ['sk-' + 'a' * 24, 'gh' + 'p_' + 'b' * 30, 'pass' + 'word: hunter2hunter2']
        for secret in fake:
            problems, _ = lint.lint_text(GOOD + f'\n{secret}\n')
            self.assertTrue(any('remove it before handing off' in m
                                for _, lv, m in problems if lv == 'error'), secret)

    def test_real_email_blocked_but_example_allowed(self):
        bad, _ = lint.lint_text(GOOD + '\ntest@realcompany.com\n')
        self.assertTrue(any('real email' in m for _, _, m in bad))
        ok, _ = lint.lint_text(GOOD + '\ntest@example.com\n')
        self.assertFalse(any('real email' in m for _, _, m in ok))

    def test_home_path_is_only_a_warning(self):
        problems, _ = lint.lint_text(GOOD + '\nsee /Users/someone/proj\n')
        self.assertTrue(any(lv == 'warning' for _, lv, _ in problems))
        self.assertFalse(any(lv == 'error' for _, lv, _ in problems))


class LintCli(ProjectCase):
    def test_clean_doc_exits_0(self):
        self.write('PROGRESS.md', GOOD)
        self.assertEqual(run('lint.py', self.root).returncode, 0)

    def test_missing_doc_exits_2(self):
        self.assertEqual(run('lint.py', self.root).returncode, 2)

    def test_bad_doc_exits_1(self):
        self.write('PROGRESS.md',
                   GOOD.replace('2. write parser tests', '2. better documentation'))
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
        self.assertEqual(run('lint.py', self.root).returncode, 0)

    def test_strict_turns_warnings_into_failure(self):
        self.write('PROGRESS.md', GOOD + '\nsee /Users/someone/proj\n')
        self.assertEqual(run('lint.py', self.root).returncode, 0)
        self.assertEqual(run('lint.py', self.root, '--strict').returncode, 1)


class LintLinks(ProjectCase):
    """Rule 11: links must resolve. Images fail, plain links warn."""

    def lint(self, extra):
        self.write('PROGRESS.md', GOOD + extra)
        return run('lint.py', self.root)

    def test_dead_image_is_an_error(self):
        out = self.lint('\n![demo](docs/missing.png)\n')
        self.assertEqual(out.returncode, 1)
        self.assertIn('image not found', out.stdout)

    def test_live_image_passes(self):
        self.write('docs/how-it-works.gif', b'GIF89a')
        out = self.lint('\n![demo](docs/how-it-works.gif)\n')
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_dead_link_warns_but_does_not_block(self):
        out = self.lint('\nsee [the deploy notes](docs/deploy.md)\n')
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn('points at a missing file', out.stdout)
        self.assertEqual(run('lint.py', self.root, '--strict').returncode, 1)

    def test_remote_and_anchor_links_are_ignored(self):
        out = self.lint('\n[a](https://example.com/x.png) [b](#next) '
                        '[c](mailto:a@example.com)\n')
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_links_in_code_fences_are_ignored(self):
        out = self.lint('\n```\n![demo](docs/missing.png)\n```\n')
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_escaping_the_project_is_not_our_business(self):
        out = self.lint('\n[repo](../elsewhere/README.md)\n')
        self.assertEqual(out.returncode, 0, out.stdout)


class ChineseDoc(ProjectCase):
    """The same code has to read a Chinese document. Headings are escapes
    here so this file itself stays free of non-ASCII prose."""

    def test_chinese_headings_are_recognised(self):
        doc = GOOD
        pairs = (
            ('One-liner', '\u4e00\u53e5\u8bdd'),
            ('Output', '\u6210\u54c1 / \u4ea7\u51fa'),
            ('Progress', '\u8fdb\u5ea6\u8868'),
            ('Where things live', '\u6587\u4ef6\u5728\u54ea'),
            ('Decisions', '\u5173\u952e\u51b3\u7b56'),
            ('Pitfalls', '\u8e29\u8fc7\u7684\u5751'),
            ('Next steps', '\u4e0b\u4e00\u6b65'),
        )
        for english, chinese in pairs:
            doc = doc.replace('## ' + english, '## ' + chinese)
        self.write('PROGRESS.md', doc)
        out = run('lint.py', self.root)
        self.assertEqual(out.returncode, 0, out.stdout)


if __name__ == '__main__':
    unittest.main()
