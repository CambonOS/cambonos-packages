"""Regression tests for cambonos-release's post_remove recovery logic."""

from __future__ import annotations

import os
import subprocess
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = ROOT / "packages/cambonos-release/cambonos-release.install"


class PostRemoveRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="cambonos-release-test-")
        self.root = Path(self.temp.name)
        self.etc = self.root / "etc"
        self.state = self.root / "var/lib/cambonos-release"
        self.etc.mkdir(parents=True)
        self.state.mkdir(parents=True)
        self.lsb = self.etc / "lsb-release"
        self.managed = self.state / "lsb-release.managed"
        self.backup = self.state / "lsb-release.original"
        self.was_absent = self.state / "lsb-release.was-absent"
        self.pacnew = self.etc / "lsb-release.pacnew"
        self.managed.write_text("DISTRIB_ID=CambonOS\n")
        self.lsb.write_text("DISTRIB_ID=CambonOS\n")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_post_remove(self, fail_command: str | None = None) -> subprocess.CompletedProcess[str]:
        script = INSTALL_SCRIPT.read_text()
        pacnew_token = "__CAMBONOS_TEST_PACNEW__"
        script = script.replace("/etc/lsb-release.pacnew", pacnew_token)
        script = script.replace("/var/lib/cambonos-release", str(self.state))
        script = script.replace("/etc/lsb-release", str(self.lsb))
        script = script.replace(pacnew_token, str(self.pacnew))
        script = script.replace("/etc/os-release", str(self.etc / "os-release"))
        script = script.replace("/etc/.lsb-release.restore.", str(self.etc / ".lsb-release.restore."))

        harness = self.root / "post-remove-test.sh"
        harness.write_text(script + "\npost_remove\n")
        env = os.environ.copy()
        if fail_command:
            fake_bin = self.root / "fake-bin"
            fake_bin.mkdir(exist_ok=True)
            command = fake_bin / fail_command
            command.write_text("#!/bin/sh\nexit 1\n")
            command.chmod(0o755)
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
        return subprocess.run(
            ["bash", str(harness)], text=True, capture_output=True, env=env, check=False
        )

    def assert_state_retained(self) -> None:
        self.assertTrue(self.state.is_dir())

    def test_restores_original_and_preserves_mode(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        self.backup.chmod(0o640)
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=Arch\n")
        self.assertEqual(self.lsb.stat().st_mode & 0o777, 0o640)
        self.assertFalse(self.state.exists())

    def test_pacnew_takes_precedence_over_original_backup(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch-old\n")
        self.pacnew.write_text("DISTRIB_ID=Arch-new\n")
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=Arch-new\n")
        self.assertFalse(self.pacnew.exists())
        self.assertFalse(self.state.exists())

    def test_pacnew_is_restored_when_original_was_absent(self) -> None:
        self.was_absent.touch()
        self.pacnew.write_text("DISTRIB_ID=Arch-from-pacnew\n")
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=Arch-from-pacnew\n")
        self.assertFalse(self.state.exists())

    def test_removes_managed_file_when_original_was_absent(self) -> None:
        self.was_absent.touch()
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.lsb.exists())
        self.assertFalse(self.state.exists())

    def test_manual_edit_is_preserved_with_recovery_state(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        self.lsb.write_text("DISTRIB_ID=Administrator\n")
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=Administrator\n")
        self.assert_state_retained()

    def test_symlink_is_preserved_with_recovery_state(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        target = self.root / "admin-lsb-release"
        target.write_text("DISTRIB_ID=Administrator\n")
        self.lsb.unlink()
        self.lsb.symlink_to(target)
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.lsb.is_symlink())
        self.assert_state_retained()

    def test_directory_is_preserved_with_recovery_state(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        self.lsb.unlink()
        self.lsb.mkdir()
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.lsb.is_dir())
        self.assert_state_retained()

    def test_missing_managed_snapshot_retains_state(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        self.managed.unlink()
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assert_state_retained()
        self.assertFalse(self.managed.exists())
        self.assertTrue(self.backup.exists())

    def test_missing_original_metadata_retains_state(self) -> None:
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assert_state_retained()

    def test_conflicting_original_markers_retain_state(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        self.was_absent.touch()
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_state_retained()

    def test_restore_failure_retains_backup_and_managed_file(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        result = self.run_post_remove(fail_command="cp")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assertEqual(self.backup.read_text(), "DISTRIB_ID=Arch\n")
        self.assert_state_retained()

    def test_temporary_directory_failure_retains_state(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        result = self.run_post_remove(fail_command="mktemp")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assert_state_retained()

    def test_atomic_replace_failure_retains_state(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        result = self.run_post_remove(fail_command="mv")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assert_state_retained()

    def test_pacnew_move_failure_retains_both_files_and_state(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        self.pacnew.write_text("DISTRIB_ID=Arch-new\n")
        result = self.run_post_remove(fail_command="mv")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assertEqual(self.pacnew.read_text(), "DISTRIB_ID=Arch-new\n")
        self.assert_state_retained()

    def test_pacnew_symlink_is_rejected_and_state_is_retained(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        target = self.root / "pacnew-target"
        target.write_text("DISTRIB_ID=Arch-new\n")
        self.pacnew.symlink_to(target)
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assertTrue(self.pacnew.is_symlink())
        self.assert_state_retained()

    def test_pacnew_directory_is_rejected_and_state_is_retained(self) -> None:
        self.was_absent.touch()
        self.pacnew.mkdir()
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assertTrue(self.pacnew.is_dir())
        self.assert_state_retained()

    def test_missing_current_lsb_file_retains_backup(self) -> None:
        self.backup.write_text("DISTRIB_ID=Arch\n")
        self.lsb.unlink()
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.lsb.exists())
        self.assertEqual(self.backup.read_text(), "DISTRIB_ID=Arch\n")
        self.assert_state_retained()

    def test_backup_directory_is_rejected_and_state_is_retained(self) -> None:
        self.backup.mkdir()
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assert_state_retained()

    def test_state_directory_symlink_is_not_followed_or_removed(self) -> None:
        external = self.root / "external-state"
        external.mkdir()
        (external / "keep").write_text("preserve\n")
        for entry in self.state.iterdir():
            if entry.is_file() or entry.is_symlink():
                entry.unlink()
            elif entry.is_dir():
                shutil.rmtree(entry)
        self.state.rmdir()
        self.state.symlink_to(external, target_is_directory=True)
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.state.is_symlink())
        self.assertEqual((external / "keep").read_text(), "preserve\n")

    def test_was_absent_directory_is_invalid_metadata(self) -> None:
        self.was_absent.mkdir()
        result = self.run_post_remove()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lsb.read_text(), "DISTRIB_ID=CambonOS\n")
        self.assert_state_retained()


if __name__ == "__main__":
    unittest.main()
