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

> Status: **in progress** · updated 2026-11-20

## One-liner
A project used by the tests.

## Output
| file | spec | note |
|---|---|---|

## Progress
| # | item | where | state |
|---|---|---|---|
| 1 | skeleton | `src/` | ✅ done |

## Where things live
- code: `src/`

## Decisions
| topic | choice | why |
|---|---|---|
| language | Python | fast |

## Pitfalls
1. none

## Next steps
1. add error handling to `src/a.py`
"""


def saving(stdout):
    """Pull the percentage out of the ledger line."""
    line = [l for l in stdout.splitlines() if l.strip().startswith('->')]
    if not line:
        return None
    m = re.search(r'(-?\d+)% cheaper than reading those (\d+) files', line[0])
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
        self.assertIn('project too small', out)
        self.assertIsNone(saving(out))

    def test_small_is_modest(self):
        self.build(28)
        self.write('PROGRESS.md', LANDING.format(name='small'))
        out = self.scan().stdout
        value = saving(out)
        self.assertIsNotNone(value)
        # The same fixture reads 71% on Windows and 68% on macOS: the token count
        # includes file paths, so the number moves with the OS. The claim here is
        # "a small repo saves far less than a large one", not a fixed percentage.
        self.assertGreaterEqual(value, 40)
        self.assertLess(value, 80)

    def test_saving_names_what_it_is_compared_against(self):
        # "cheaper than typical" was read as "cheaper than your agent would
        # have spent". It is cheaper than one modelled pickup, so say which.
        self.build(180, n_docs=8, body=90)
        self.write('PROGRESS.md', LANDING.format(name='large'))
        line = [l for l in self.scan().stdout.splitlines() if l.strip().startswith('->')]
        self.assertRegex(line[0], r'cheaper than reading those \d+ files')

    def test_large_is_big(self):
        self.build(180, n_docs=8, body=90)
        self.write('PROGRESS.md', LANDING.format(name='large'))
        out = self.scan().stdout
        self.assertGreaterEqual(saving(out), 85)


if __name__ == '__main__':
    unittest.main()
