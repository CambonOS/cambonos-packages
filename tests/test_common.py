from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.common import (
    CambonosError, atomic_write, compare_arch_versions, require_commands,
    run_command, sha256_directory, sha256_file,
)


class CommonTests(unittest.TestCase):
    def test_sha256_file_matches_standard_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "payload.bin"
            path.write_bytes(b"CambonOS\x00payload")
            self.assertEqual(sha256_file(path), hashlib.sha256(path.read_bytes()).hexdigest())

    def test_sha256_directory_is_independent_of_creation_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            left, right = root / "left", root / "right"
            left.mkdir(); right.mkdir()
            (left / "b").write_text("B")
            (left / "a").write_text("A")
            (right / "a").write_text("A")
            (right / "b").write_text("B")
            self.assertEqual(sha256_directory(left), sha256_directory(right))

    def test_sha256_directory_changes_when_mode_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "script"
            path.write_text("#!/bin/sh\n")
            first = sha256_directory(root)
            path.chmod(0o755)
            self.assertNotEqual(first, sha256_directory(root))

    def test_sha256_directory_includes_symlink_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "target").write_text("one")
            (root / "link").symlink_to("target")
            first = sha256_directory(root)
            (root / "link").unlink()
            (root / "link").symlink_to("missing")
            self.assertNotEqual(first, sha256_directory(root))

    def test_sha256_directory_excludes_build_outputs_and_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "PKGBUILD").write_text("pkgrel=1")
            first = sha256_directory(root)
            for name in ("src", "pkg", ".git", "__pycache__", ".pytest_cache"):
                (root / name).mkdir()
                (root / name / "generated").write_text("ignored")
            self.assertEqual(first, sha256_directory(root))

    def test_atomic_write_replaces_existing_content_and_creates_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "nested" / "state.txt"
            atomic_write(target, "new state\n")
            self.assertEqual(target.read_text(), "new state\n")
            self.assertFalse(target.with_name(target.name + ".tmp").exists())

    def test_require_commands_reports_all_missing_commands(self):
        with patch("cambonos_lib.common.shutil.which", return_value=None):
            with self.assertRaisesRegex(CambonosError, "missing-a, missing-b"):
                require_commands("missing-a", "missing-b")

    def test_run_command_captures_output_and_input(self):
        result = run_command(
            [sys.executable, "-c", "import sys; print(sys.stdin.read())"],
            capture=True, input_text="hello",
        )
        self.assertEqual(result.stdout, "hello\n")

    def test_run_command_wraps_missing_executable(self):
        with self.assertRaisesRegex(CambonosError, "no se encuentra el comando"):
            run_command(["/definitely/not/a/command"])

    def test_run_command_reports_nonzero_exit_when_checking(self):
        with self.assertRaisesRegex(CambonosError, r"comando fallido \(7\)"):
            run_command([sys.executable, "-c", "raise SystemExit(7)"], capture=True)

    def test_run_command_can_return_nonzero_when_check_disabled(self):
        result = run_command(
            [sys.executable, "-c", "raise SystemExit(7)"], check=False
        )
        self.assertEqual(result.returncode, 7)

    def test_compare_arch_versions_uses_host_vercmp_when_available(self):
        with patch("cambonos_lib.common.shutil.which", return_value="/usr/bin/vercmp"), \
             patch("cambonos_lib.common.run_command") as run:
            run.return_value.stdout = "-1\n"
            self.assertEqual(compare_arch_versions("1-2", "1-3", "unused"), -1)
            run.assert_called_once_with(["vercmp", "1-2", "1-3"], capture=True)

    def test_compare_arch_versions_rejects_unexpected_vercmp_output(self):
        with patch("cambonos_lib.common.shutil.which", return_value="/usr/bin/vercmp"), \
             patch("cambonos_lib.common.run_command") as run:
            run.return_value.stdout = "not-an-integer"
            with self.assertRaises(CambonosError):
                compare_arch_versions("1-1", "1-2", "unused")


if __name__ == "__main__":
    unittest.main()
