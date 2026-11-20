"""scan.py: inventory, skipping, token ledger, JSON."""

import json
import os
import sys
import unittest

from _util import SCRIPTS, ProjectCase, run

sys.path.insert(0, SCRIPTS)
import scan  # noqa: E402


class ScanUnit(unittest.TestCase):
    def test_est_tokens_english_and_cjk(self):
        # 校准值：0.2510 tok/ASCII 字符，1.6876 tok/中文字
        self.assertAlmostEqual(scan.est_tokens('a' * 400), 100, delta=4)
        self.assertAlmostEqual(scan.est_tokens('中' * 60), 101, delta=5)

    def test_est_tokens_is_additive(self):
        a, b = scan.est_tokens('abc'), scan.est_tokens('中文')
        self.assertAlmostEqual(scan.est_tokens('abc中文'), a + b, places=6)

    def test_brief_factor_only_applies_to_heuristic(self):
        self.assertGreater(scan.BRIEF_TEXT_FACTOR, 1.0)

    def test_bulk_files_are_not_text(self):
        self.assertEqual(scan.text_key('package-lock.json'), '')
        self.assertEqual(scan.text_key('app.min.js'), '')
        self.assertEqual(scan.text_key('a.py'), '.py')


class ScanCli(ProjectCase):
    def test_skips_node_modules_and_build_dirs(self):
        self.write('src/a.ts', 'export const a = 1;\n')
        self.write('node_modules/x/big.js', 'y' * 5000)
        self.write('.next/cache.js', 'z' * 5000)
        out = self.scan().stdout
        self.assertIn('files: 1', out)

    def test_small_project_advice(self):
        self.write('README.md', '# hi\n')
        self.write('a.py', 'print(1)\n')
        out = self.scan().stdout
        self.assertIn('直接读 README 更快', out)
        self.assertIn('写文档比直接读还贵', out)
        self.assertNotIn('-', out.split('→')[1].split('tok')[0])

    def test_progress_doc_is_detected_with_age(self):
        self.write('src/a.py', 'x = 1\n')
        self.write('PROGRESS.md', '# p\n')
        out = self.scan().stdout
        self.assertIn('PROGRESS.md  (2 lines, 0d old)', out)

    def test_json_shape(self):
        self.write('src/a.py', 'x = 1\n')
        data = json.loads(self.scan('--json').stdout)
        for key in ('root', 'files', 'text_files', 'tokens'):
            self.assertIn(key, data)
        for key in ('worst', 'typical', 'brief'):
            self.assertIn(key, data['tokens'])

    def test_no_ledger_writes_nothing(self):
        self.write('a.py', 'x = 1\n')
        self.scan()
        self.assertFalse(os.path.exists(self.ledger))

    def test_ledger_accumulates(self):
        self.write('a.py', 'x = 1\n')
        first = run('scan.py', self.root, env=self.env)
        self.assertTrue(os.path.exists(self.ledger))
        second = run('scan.py', self.root, env=self.env)
        self.assertIn('累计 2 次运行', second.stdout)
        self.assertEqual(first.returncode, 0)

    def test_broken_ledger_line_is_ignored(self):
        self.write('a.py', 'x = 1\n')
        run('scan.py', self.root, env=self.env)
        with open(self.ledger, 'a', encoding='utf-8') as fh:
            fh.write('not json{{\n')
        out = run('scan.py', self.root, env=self.env)
        self.assertEqual(out.returncode, 0)
        self.assertIn('累计', out.stdout)

    def test_empty_dir_does_not_crash(self):
        out = self.scan()
        self.assertEqual(out.returncode, 0)
        self.assertIn('files: 0', out.stdout)


if __name__ == '__main__':
    unittest.main()
