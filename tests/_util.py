"""Shared helpers for the test suite. Stdlib only."""

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'scripts')
sys.path.insert(0, SCRIPTS)


def run(script, *args, cwd=None, env=None):
    """Run a script as a subprocess with a pinned tokenizer."""
    e = dict(os.environ)
    e['PROGRESS_BRIEF_TOKENIZER'] = 'heuristic'
    e['PYTHONIOENCODING'] = 'utf-8'
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script), *args],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        cwd=cwd, env=e,
    )


class ProjectCase(unittest.TestCase):
    """Temp project with its own ledger file."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.ledger = os.path.join(self.root, '.ledger.jsonl')
        self.env = {'PROGRESS_BRIEF_LEDGER': self.ledger}

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path) or self.root, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)
        return path

    def scan(self, *args):
        return run('scan.py', self.root, '--no-ledger', *args, env=self.env)

    def doctor(self, *args):
        return run('doctor.py', self.root, *args, env=self.env)
