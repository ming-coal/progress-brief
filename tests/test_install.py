"""install.py: where it puts things, and that it is idempotent."""

import os
import sys
import unittest

from _util import ROOT, SCRIPTS, ProjectCase, run

sys.path.insert(0, SCRIPTS)
import install  # noqa: E402


class Install(ProjectCase):
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

    def test_copies_skill_and_scripts(self):
        out = run('install.py', '--project', self.root)
        self.assertEqual(out.returncode, 0)
        base = os.path.join(self.root, '.opencode', 'skills', 'progress-brief')
        for rel in ('SKILL.md', 'scripts/scan.py', 'scripts/doctor.py',
                    'scripts/card.py', 'scripts/lint.py', 'scripts/install.py'):
            self.assertTrue(os.path.exists(os.path.join(base, rel)), rel)

    def test_rerun_is_idempotent(self):
        run('install.py', '--project', self.root)
        out = run('install.py', '--project', self.root)
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
        self.assertFalse(os.path.exists(os.path.join(ROOT, '.opencode')))


class Platform(unittest.TestCase):
    def test_windows_uses_appdata(self):
        from pathlib import Path
        real_name, real_path = os.name, install.Path
        install.Path = type(Path('/'))     # 只验证分支，不真造 WindowsPath
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
