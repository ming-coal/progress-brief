"""The documented rule count has to match the code.

0.1.0 said "11 rules" while `RULES` held ten. Nobody noticed because nothing
compared the sentence with the list. Now something does.
"""

import os
import re
import sys
import unittest

from _util import ROOT, SCRIPTS

sys.path.insert(0, SCRIPTS)
import lint  # noqa: E402


class RuleCount(unittest.TestCase):
    def counts_in(self, name):
        with open(os.path.join(ROOT, name), encoding='utf-8') as fh:
            text = fh.read()
        return [int(n) for n in re.findall(r'(\d+)\s+rules?\b', text)]

    def test_progress_md_matches_the_code(self):
        counts = self.counts_in('PROGRESS.md')
        self.assertTrue(counts, 'PROGRESS.md no longer states a rule count')
        for n in counts:
            self.assertEqual(n, len(lint.RULES),
                             f'PROGRESS.md says {n}, lint.py has {len(lint.RULES)}')

    def test_rule_keys_are_unique(self):
        keys = [k for k, _ in lint.RULES]
        self.assertEqual(len(keys), len(set(keys)))

    def test_every_rule_has_a_description(self):
        for key, desc in lint.RULES:
            self.assertTrue(desc.strip(), key)

    def test_rules_flag_lists_every_rule(self):
        from _util import run
        out = run('lint.py', '--rules')
        self.assertEqual(out.returncode, 0)
        for key, _ in lint.RULES:
            self.assertIn(key, out.stdout)


if __name__ == '__main__':
    unittest.main()
