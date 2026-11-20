"""card.py: HTML building and CLI failure modes."""

import os
import re
import sys
import unittest

from _util import SCRIPTS, ProjectCase, run

sys.path.insert(0, SCRIPTS)
import card  # noqa: E402


class CardBuild(unittest.TestCase):
    def test_escapes_html(self):
        html = card.build({'title': '<script>alert(1)</script>'})
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_empty_status_renders_no_pill(self):
        html = card.build({'title': 'x'})
        self.assertNotIn('class="status"', html)

    def test_empty_stats_render_nothing(self):
        html = card.build({'title': 'x'})
        self.assertNotIn('class="stats"', html)

    def test_highlight_wraps_first_occurrence_only(self):
        html = card.build({'title': '上线前上线后', 'highlight': ['上线']})
        self.assertEqual(html.count('<em>上线</em>'), 1)

    def test_long_title_shrinks_font(self):
        short = int(re.search(r'<h1 style="font-size:(\d+)px"',
                              card.build({'title': '短'})).group(1))
        long = int(re.search(r'<h1 style="font-size:(\d+)px"',
                             card.build({'title': '很长的标题' * 8})).group(1))
        self.assertLess(long, short)
        self.assertGreaterEqual(long, 36)


class CardCli(ProjectCase):
    def test_bad_json_is_a_clean_error(self):
        path = self.write('bad.json', '{oops')
        out = run('card.py', path)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('不是合法 JSON', out.stderr)
        self.assertNotIn('Traceback', out.stderr)

    def test_missing_file_is_a_clean_error(self):
        out = run('card.py', os.path.join(self.root, 'nope.json'))
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('找不到', out.stderr)

    def test_writes_html_even_without_browser(self):
        path = self.write('s.json', '{"title":"x"}')
        run('card.py', path, env={'PATH': ''})
        self.assertTrue(os.path.exists(os.path.join(self.root, 's.html')))


if __name__ == '__main__':
    unittest.main()
