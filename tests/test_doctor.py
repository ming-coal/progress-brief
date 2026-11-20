"""doctor.py: the three verdicts and their exit codes."""

import json
import os
import unittest

from _util import ProjectCase


class Doctor(ProjectCase):
    def many_sources(self, n=20):
        for i in range(n):
            self.write(f'src/mod{i}.py', f'x = {i}\n')

    def test_no_doc_large_project_exits_2(self):
        self.many_sources()
        out = self.doctor()
        self.assertEqual(out.returncode, 2)
        self.assertIn('no handoff doc', out.stdout)

    def test_no_doc_tiny_project_exits_0(self):
        self.write('a.py', 'x = 1\n')
        out = self.doctor()
        self.assertEqual(out.returncode, 0)
        self.assertIn('no doc needed', out.stdout)

    def test_fresh_doc_exits_0(self):
        self.many_sources()
        self.write('PROGRESS.md', '# p\n## Next steps\n1. a\n')
        out = self.doctor()
        self.assertEqual(out.returncode, 0)
        self.assertIn('the doc is fresh', out.stdout)

    def test_drift_exits_1(self):
        self.many_sources()
        doc = self.write('PROGRESS.md', '# p\n')
        os.utime(doc, (0, 0))  # pretend the doc is ancient
        out = self.doctor()
        self.assertEqual(out.returncode, 1)
        self.assertIn('drift', out.stdout)

    def test_overlong_doc_exits_1(self):
        self.write('src/a.py', 'x = 1\n')
        self.write('PROGRESS.md', 'line\n' * 130)
        out = self.doctor()
        self.assertEqual(out.returncode, 1)
        self.assertIn('over 120', out.stdout)

    def test_json_output(self):
        self.many_sources()
        self.write('PROGRESS.md', '# p\n')
        out = self.doctor('--json')
        data = json.loads(out.stdout)
        self.assertEqual(data['code'], 0)
        self.assertEqual(data['doc'], 'PROGRESS.md')
        self.assertIn('verdict', data)

    def test_quiet_hides_advice(self):
        self.write('a.py', 'x = 1\n')
        out = self.doctor('--quiet')
        self.assertNotIn('window hygiene', out.stdout)


if __name__ == '__main__':
    unittest.main()
