"""install.py: targets, arbitrary destinations, AGENTS.md wiring."""

import os
import sys
import unittest
from pathlib import Path

from _util import ROOT, SCRIPTS, ProjectCase, run

sys.path.insert(0, SCRIPTS)
import install  # noqa: E402


class Target(ProjectCase):
    def test_project_target_layout(self):
        dest = install.target_dir(self.root)
        self.assertTrue(str(dest).endswith(
            os.path.join('.opencode', 'skills', 'progress-brief')))
        self.assertTrue(str(dest).startswith(os.path.realpath(self.root)))

    def test_global_target_defaults_to_opencode(self):
        dest = str(install.target_dir())
        self.assertTrue(dest.endswith(os.path.join('progress-brief')))
        self.assertIn('opencode', dest)

    def test_claude_target(self):
        dest = str(install.target_dir(target='claude'))
        self.assertTrue(dest.endswith(os.path.join('.claude', 'skills', 'progress-brief')),
                        dest)

    def test_dest_is_taken_literally(self):
        """Any agent: point --dest at a folder and it is used verbatim."""
        dest = install.target_dir(dest=os.path.join(self.root, 'tools', 'pb'))
        self.assertEqual(os.path.realpath(str(dest)),
                         os.path.realpath(os.path.join(self.root, 'tools', 'pb')))


class Install(ProjectCase):
    def test_copies_skill_and_scripts(self):
        dest = os.path.join(self.root, 'pb')
        out = run('install.py', '--dest', dest)
        self.assertEqual(out.returncode, 0)
        for rel in ('SKILL.md', 'scripts/scan.py', 'scripts/doctor.py',
                    'scripts/card.py', 'scripts/lint.py', 'scripts/install.py'):
            self.assertTrue(os.path.exists(os.path.join(dest, rel)), rel)

    def test_rerun_is_idempotent(self):
        dest = os.path.join(self.root, 'pb')
        run('install.py', '--dest', dest)
        out = run('install.py', '--dest', dest)
        self.assertEqual(out.returncode, 0)
        self.assertIn('installed', out.stdout)

    def test_dry_run_writes_nothing(self):
        out = run('install.py', '--project', self.root, '--dry-run')
        self.assertEqual(out.returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.root, '.opencode')))

    def test_refuses_to_install_into_itself(self):
        out = run('install.py', '--project', ROOT)
        self.assertEqual(out.returncode, 1)
        self.assertIn('refusing', out.stdout)

    def test_rejects_unknown_target(self):
        out = run('install.py', '--target', 'cursor', '--dry-run')
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('--dest', out.stderr)


class UniversalPrompt(ProjectCase):
    def test_prompt_mentions_every_step(self):
        out = run('install.py', '--prompt')
        self.assertEqual(out.returncode, 0)
        for needle in ('doctor.py', 'scan.py', 'lint.py', 'PROGRESS.md', '120 lines'):
            self.assertIn(needle, out.stdout)

    def test_agents_md_is_created_and_wired(self):
        dest = os.path.join(self.root, 'pb')
        target = os.path.join(self.root, 'AGENTS.md')
        run('install.py', '--dest', dest, '--agents-md', target)
        text = open(target, encoding='utf-8').read()
        self.assertIn('progress-brief:start', text)
        # Windows gives tempfile a 8.3 short path (RUNNER~1); install.py resolves it
        self.assertIn(str(Path(dest).resolve()), text)
        self.assertIn('lint.py', text)

    def test_agents_md_rerun_does_not_duplicate(self):
        dest = os.path.join(self.root, 'pb')
        target = os.path.join(self.root, 'AGENTS.md')
        with open(target, 'w', encoding='utf-8') as fh:
            fh.write('# Project\n\nKeep me.\n')
        run('install.py', '--dest', dest, '--agents-md', target)
        run('install.py', '--dest', dest, '--agents-md', target)
        text = open(target, encoding='utf-8').read()
        self.assertEqual(text.count('progress-brief:start'), 1)
        self.assertIn('Keep me.', text)

    def test_agents_md_preserves_surrounding_text(self):
        dest = os.path.join(self.root, 'pb')
        target = os.path.join(self.root, 'AGENTS.md')
        with open(target, 'w', encoding='utf-8') as fh:
            fh.write('# Before\n\ntext\n')
        run('install.py', '--dest', dest, '--agents-md', target)
        text = open(target, encoding='utf-8').read() + '\n# After\n'
        with open(target, 'w', encoding='utf-8') as fh:
            fh.write(text)
        run('install.py', '--dest', dest, '--agents-md', target)
        text = open(target, encoding='utf-8').read()
        self.assertIn('# Before', text)
        self.assertIn('# After', text)


class Platform(unittest.TestCase):
    def test_windows_uses_appdata(self):
        real_name, real_path = os.name, install.Path
        install.Path = type(Path('/'))
        os.environ['APPDATA'] = '/tmp/fake-appdata'
        os.environ.pop('XDG_CONFIG_HOME', None)
        try:
            os.name = 'nt'
            dirs = [str(p) for p in install.opencode_config_dirs()]
        finally:
            os.name = real_name
            install.Path = real_path
        self.assertTrue(any('fake-appdata' in d for d in dirs))


if __name__ == '__main__':
    unittest.main()
