from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.common import CambonosError
from cambonos_lib.repository import create_repository


class RepositoryTests(unittest.TestCase):
    def _build_root(self, root: Path, names=("sample-1-1-any.pkg.tar.zst",)) -> Path:
        packages = root / "packages"
        packages.mkdir(parents=True)
        for name in names:
            (packages / name).write_bytes(name.encode())
        return root

    @patch("cambonos_lib.repository.require_commands")
    @patch("cambonos_lib.repository.run_command")
    def test_creates_stable_repository_and_database_aliases(self, run, _require):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "build"
            self._build_root(root)
            destination = Path(temporary) / "site" / "stable" / "x86_64"

            def make_database(command):
                # Simulate repo-add's output inside the bind-mounted destination.
                destination.joinpath("cambonos.db.tar.gz").write_bytes(b"db")
                destination.joinpath("cambonos.files.tar.gz").write_bytes(b"files")
            run.side_effect = make_database
            archives = create_repository(root, destination, "stable", "arch-image")

            self.assertEqual([p.name for p in archives], ["sample-1-1-any.pkg.tar.zst"])
            self.assertEqual((destination / "sample-1-1-any.pkg.tar.zst").read_bytes(),
                             b"sample-1-1-any.pkg.tar.zst")
            self.assertEqual((destination / "cambonos.db").read_bytes(), b"db")
            self.assertEqual((destination / "cambonos.files").read_bytes(), b"files")
            command = run.call_args.args[0]
            self.assertIn("--network", command)
            self.assertIn("none", command)
            self.assertIn("repo-add --include-sigs", command[-1])

    @patch("cambonos_lib.repository.require_commands")
    @patch("cambonos_lib.repository.run_command")
    def test_copies_existing_package_signature(self, run, _require):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "build"
            self._build_root(root)
            archive = root / "packages" / "sample-1-1-any.pkg.tar.zst"
            Path(str(archive) + ".sig").write_bytes(b"signature")
            destination = Path(temporary) / "repo"
            def make_database(_command):
                for name in ("cambonos-testing.db.tar.gz", "cambonos-testing.files.tar.gz"):
                    (destination / name).write_bytes(name.encode())
            run.side_effect = make_database
            create_repository(root, destination, "testing", "arch-image")
            self.assertEqual(
                Path(str(destination / archive.name) + ".sig").read_bytes(), b"signature"
            )
            self.assertTrue((destination / "cambonos-testing.db").is_file())

    @patch("cambonos_lib.repository.require_commands")
    def test_empty_package_directory_fails(self, _require):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / "packages").mkdir()
            with self.assertRaisesRegex(CambonosError, "no hay paquetes"):
                create_repository(root, root / "repo", "stable", "image")

    @patch("cambonos_lib.repository.require_commands")
    def test_non_zstd_archive_fails_before_docker(self, _require):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / "packages").mkdir()
            (root / "packages" / "sample.pkg.tar.xz").write_bytes(b"x")
            with patch("cambonos_lib.repository.run_command") as run:
                with self.assertRaisesRegex(CambonosError, "solo se admiten paquetes zstd"):
                    create_repository(root, root / "repo", "stable", "image")
                run.assert_not_called()

    @patch("cambonos_lib.repository.require_commands")
    @patch("cambonos_lib.repository.run_command")
    def test_missing_repo_add_database_fails(self, run, _require):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "build"
            self._build_root(root)
            destination = Path(temporary) / "repo"
            with self.assertRaisesRegex(CambonosError, "repo-add no generó"):
                create_repository(root, destination, "stable", "image")

    @patch("cambonos_lib.repository.require_commands")
    @patch("cambonos_lib.repository.run_command", side_effect=CambonosError("repo-add failed"))
    def test_repo_add_failure_propagates(self, _run, _require):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "build"
            self._build_root(root)
            with self.assertRaisesRegex(CambonosError, "repo-add failed"):
                create_repository(root, Path(temporary) / "repo", "stable", "image")


if __name__ == "__main__":
    unittest.main()
