import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/install_project_agents.py"
ROLES = sorted((ROOT / ".codex/agents").glob("*.toml"))


class ProjectAgentInstallerTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory(dir="/private/tmp")
        self.addCleanup(scratch.cleanup)
        self.base = Path(scratch.name)
        self.main = self.base / "Moneyfesting"
        self.main.mkdir()
        self.git(self.main, "init", "-b", "master")
        self.git(self.main, "-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "commit", "--allow-empty", "-m", "initial")
        self.worktree = self.base / "Moneyfesting-wt" / "localization-readiness"
        self.worktree.parent.mkdir()
        self.git(self.main, "worktree", "add", "-b", "i18n/localization-readiness",
                 str(self.worktree), "master")

    def git(self, root, *args):
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              capture_output=True, text=True)

    def command(self, root=None, *options, success=True):
        result = subprocess.run([sys.executable, str(INSTALLER), "--app-root",
                                 str(root or self.worktree), *options],
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def test_preflight_then_install_and_identical_rerun(self):
        destination = self.worktree / ".codex/agents"
        preview = self.command()
        self.assertEqual(preview.stdout.count("new: "), 9)
        self.assertFalse(destination.exists())
        self.command(None, "--apply")
        self.assertEqual({path.name for path in destination.glob("*.toml")},
                         {path.name for path in ROLES})
        for source in ROLES:
            self.assertEqual((destination / source.name).read_bytes(), source.read_bytes())
        rerun = self.command(None, "--apply")
        self.assertEqual(rerun.stdout.count("unchanged: "), 9)

    def test_rejects_main_checkout_and_non_i18n_branch(self):
        self.command(self.main, "--apply", success=False)
        self.assertFalse((self.main / ".codex").exists())
        self.git(self.worktree, "branch", "-m", "other")
        self.command(None, "--apply", success=False)
        self.assertFalse((self.worktree / ".codex").exists())

    def test_rejects_wrong_location_and_symlink_alias(self):
        misplaced = self.base / "other" / "topic"
        misplaced.parent.mkdir()
        self.git(self.main, "worktree", "add", "-b", "i18n/other", str(misplaced), "master")
        self.command(misplaced, "--apply", success=False)
        alias = self.base / "alias"
        alias.symlink_to(self.worktree, target_is_directory=True)
        self.command(alias, "--apply", success=False)
        self.assertFalse((self.worktree / ".codex").exists())

    def test_conflict_preserves_all_files_and_prevents_partial_install(self):
        destination = self.worktree / ".codex/agents"
        destination.mkdir(parents=True)
        conflicting = destination / ROLES[0].name
        conflicting.write_text("owner version\n")
        unrelated = destination / "owner_role.toml"
        unrelated.write_text("owner role\n")
        result = self.command(None, "--apply", success=False)
        self.assertIn("conflicting:", result.stdout)
        self.assertIn("unrelated (preserved): owner_role.toml", result.stdout)
        self.assertEqual(conflicting.read_text(), "owner version\n")
        self.assertEqual(unrelated.read_text(), "owner role\n")
        self.assertEqual(len(list(destination.iterdir())), 2)

    def test_rejects_symlink_destination_directory_and_role(self):
        outside = self.base / "outside"
        outside.mkdir()
        codex = self.worktree / ".codex"
        codex.symlink_to(outside, target_is_directory=True)
        self.command(None, "--apply", success=False)
        self.assertEqual(list(outside.iterdir()), [])
        codex.unlink()
        destination = codex / "agents"
        destination.mkdir(parents=True)
        (destination / ROLES[0].name).symlink_to(outside / "role.toml")
        self.command(None, "--apply", success=False)
        self.assertEqual(len(list(destination.iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
