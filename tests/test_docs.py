"""The test count printed in the docs has to be the real one.

It has been wrong four times: 61 while 63 ran, 55 in the README for three
releases, 76 in a card PNG. Numbers in prose are the one thing lint.py
cannot check, so they are checked here instead. The count is static
(`def test_` in this directory), which keeps the assertion from depending
on how discovery happens to run.
"""

import glob
import json
import os
import re
import unittest

from _util import ROOT

# Patterns per file, each with exactly one capturing group.
CLAIMS = {
    'README.md': [r'(\d+) stdlib tests'],
    # Escapes, not CJK: tests/test_no_cjk.py keeps this directory ASCII.
    'README.zh-CN.md': [r'(\d+) ' + '\u4e2a\u6807\u51c6\u5e93\u6d4b\u8bd5'],
    'PROGRESS.md': [r'\| `tests/` \| (\d+) tests'],
    'CONTRIBUTING.md': [r'(\d+) tests, about'],
    'docs/launch.md': [r'(\d+) tests', r'tests: (\d+)'],
    'examples/status.json': [r'(\d+) tests'],
}
# CHANGELOG.md is deliberately absent: its entries are history and must not be
# rewritten when the count moves.


def count_tests():
    total = 0
    for path in glob.glob(os.path.join(ROOT, 'tests', 'test_*.py')):
        with open(path, encoding='utf-8') as fh:
            total += len(re.findall(r'(?m)^\s+def test_\w+', fh.read()))
    return total


class DocumentedNumbers(unittest.TestCase):
    def test_every_doc_quotes_the_real_test_count(self):
        real = count_tests()
        wrong = []
        for rel, patterns in CLAIMS.items():
            path = os.path.join(ROOT, rel)
            text = open(path, encoding='utf-8').read()
            if rel.endswith('.json'):
                text = json.dumps(json.loads(text), ensure_ascii=False)
            for pattern in patterns:
                found = re.findall(pattern, text)
                if not found:
                    wrong.append(f'{rel}: no claim matched {pattern!r}')
                for value in found:
                    if int(value) != real:
                        wrong.append(f'{rel}: says {value}, {real} tests exist')
        self.assertEqual(wrong, [], '\n'.join(wrong))

    def test_ci_matrix_matches_what_the_readme_promises(self):
        workflow = open(os.path.join(ROOT, '.github/workflows/test.yml'),
                        encoding='utf-8').read()
        runs = re.search(r'os: \[([^\]]+)\]', workflow).group(1).split(',')
        pythons = re.search(r"python: \[([^\]]+)\]", workflow).group(1).split(',')
        readme = open(os.path.join(ROOT, 'README.md'), encoding='utf-8').read()
        claim = re.search(r'CI on (\d+) OS . (\d+) Python versions', readme)
        self.assertIsNotNone(claim, 'the README stopped promising a CI matrix')
        self.assertEqual(int(claim.group(1)), len(runs))
        self.assertEqual(int(claim.group(2)), len(pythons))


if __name__ == '__main__':
    unittest.main()
