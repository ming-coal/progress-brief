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
        html = card.build({'title': 'ship it, ship it again', 'highlight': ['ship']})
        self.assertEqual(html.count('<em>ship</em>'), 1)

    def test_long_title_shrinks_font(self):
        short = int(re.search(r'<h1 style="font-size:(\d+)px"',
                              card.build({'title': 'short'})).group(1))
        long = int(re.search(r'<h1 style="font-size:(\d+)px"',
                             card.build({'title': 'a very long title ' * 8})).group(1))
        self.assertLess(long, short)
        self.assertGreaterEqual(long, 36)

    def test_font_stack_has_cjk_fallbacks_for_every_os(self):
        # PingFang ships with macOS only. Without the other two, a Chinese title
        # renders in a browser-chosen fallback on Windows and Linux.
        stack = re.search(r'font-family:([^;]+)', card.build({'title': 'x'})).group(1)
        for family in ('PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC'):
            self.assertIn(family, stack)


class CardCli(ProjectCase):
    def test_bad_json_is_a_clean_error(self):
        path = self.write('bad.json', '{oops')
        out = run('card.py', path)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('is not valid JSON', out.stderr)
        self.assertNotIn('Traceback', out.stderr)

    def test_missing_file_is_a_clean_error(self):
        out = run('card.py', os.path.join(self.root, 'nope.json'))
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('not found', out.stderr)

    def test_writes_html_even_without_browser(self):
        path = self.write('s.json', '{"title":"x"}')
        run('card.py', path, env={'PATH': ''})
        self.assertTrue(os.path.exists(os.path.join(self.root, 's.html')))

    def test_failed_screenshot_is_not_reported_as_success(self):
        # A browser that exists but cannot render: python exits non-zero and
        # writes nothing. The old png must survive and the run must say so.
        old = self.write('s.png', b'previous render')
        path = self.write('s.json', '{"title":"x"}')
        out = run('card.py', path, env={'PROGRESS_BRIEF_CHROME': sys.executable})
        self.assertIn('screenshot failed', out.stdout)
        self.assertNotIn('png  ', out.stdout)
        with open(old, 'rb') as fh:
            self.assertEqual(fh.read(), b'previous render')


if __name__ == '__main__':
    unittest.main()
