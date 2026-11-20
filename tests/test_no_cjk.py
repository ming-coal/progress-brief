"""No Chinese anywhere in code or tests.

The linter still has to read Chinese documents, so exactly one block in
`lint.py` — the bilingual vocabulary — is allowed to hold non-ASCII. That is
data the tool needs, not prose. Everything else has to be English: comments,
docstrings, printed messages, fixtures.

CJK samples in tests are written as escapes (\\u4e2d) so the files stay ASCII.
"""

import os
import re
import unittest

from _util import ROOT

# CJK ideographs plus CJK and fullwidth punctuation
CJK = re.compile(r'[\u3000-\u303f\u3400-\u9fff\uf900-\ufaff\uff00-\uffef]')
VOCAB_START = 'bilingual vocabulary (data, not prose)'
VOCAB_END = 'end bilingual vocabulary'


def strip_vocab(text):
    kept, inside = [], False
    for line in text.splitlines():
        if VOCAB_START in line:
            inside = True
            continue
        if VOCAB_END in line:
            inside = False
            continue
        if not inside:
            kept.append(line)
    return '\n'.join(kept)


class NoChinese(unittest.TestCase):
    def py_files(self):
        for base, dirs, names in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__')]
            for n in names:
                if n.endswith('.py'):
                    yield os.path.join(base, n)

    def test_no_cjk_in_python(self):
        offenders = {}
        for path in self.py_files():
            with open(path, encoding='utf-8') as fh:
                text = strip_vocab(fh.read())
            hits = [(i, line.strip()) for i, line in enumerate(text.splitlines(), 1)
                    if CJK.search(line)]
            if hits:
                offenders[os.path.relpath(path, ROOT)] = hits[:3]
        self.assertEqual(offenders, {}, 'non-English text found in code or tests')

    def test_the_vocabulary_block_still_exists(self):
        path = os.path.join(ROOT, 'scripts', 'lint.py')
        with open(path, encoding='utf-8') as fh:
            text = fh.read()
        self.assertIn(VOCAB_START, text)
        self.assertIn(VOCAB_END, text)
        self.assertTrue(CJK.search(text), 'the vocabulary should hold the CJK keywords')


if __name__ == '__main__':
    unittest.main()
