from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.cambonos_lib.common import CambonosError
from scripts.cambonos_lib.external_dispatch import validate_external_dispatch
from scripts.stage_external_packages import stage_external_package


class ExternalDispatchTests(unittest.TestCase):
    def test_installer_dev_targets_testing(self):
        self.assertEqual(
            validate_external_dispatch(
                "CambonOS/cambonos-installer", "cambonos-installer", "dev", "a" * 40
            ),
            "testing",
        )

    def test_mkiso_main_targets_stable(self):
        self.assertEqual(
            validate_external_dispatch(
                "CambonOS/cambonos-mkiso", "cambonos-mkiso", "main", "b" * 40
            ),
            "stable",
        )

    def test_unknown_repository_is_rejected(self):
        with self.assertRaisesRegex(CambonosError, "no autorizado"):
            validate_external_dispatch("someone/else", "cambonos-installer", "dev", "a" * 40)

    def test_repository_cannot_claim_another_package(self):
        with self.assertRaisesRegex(CambonosError, "no puede notificar"):
            validate_external_dispatch(
                "CambonOS/cambonos-installer", "cambonos-mkiso", "dev", "a" * 40
            )

    def test_unsupported_branch_is_rejected(self):
        with self.assertRaisesRegex(CambonosError, "rama externa"):
            validate_external_dispatch(
                "CambonOS/cambonos-installer", "cambonos-installer", "feature", "a" * 40
            )

    def test_malformed_commit_is_rejected(self):
        with self.assertRaisesRegex(CambonosError, "SHA"):
            validate_external_dispatch(
                "CambonOS/cambonos-installer", "cambonos-installer", "dev", "not-a-sha"
            )


class ExternalSourceProvenanceTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()

    def _commit(self, source: Path, message: str) -> str:
        self._git(source, "add", "PKGBUILD", "LICENSE", "README.md", "files")
        self._git(source, "commit", "-m", message)
        return self._git(source, "rev-parse", "HEAD")

    def test_documentation_commit_does_not_change_package_source_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            self._git(source, "init", "-q")
            self._git(source, "config", "user.name", "CambonOS test")
            self._git(source, "config", "user.email", "test@example.invalid")
            self._git(
                source, "remote", "add", "origin",
                "https://github.com/CambonOS/cambonos-installer.git",
            )
            (source / "PKGBUILD").write_text(
                "pkgname=cambonos-installer\npkgver=1.0.0\npkgrel=1\n"
                "arch=('any')\npackage() { :; }\n",
                encoding="utf-8",
            )
            (source / "LICENSE").write_text("license v1\n", encoding="utf-8")
            (source / "README.md").write_text("documentation v1\n", encoding="utf-8")
            (source / "files").mkdir()
            (source / "files/installer").write_text("payload v1\n", encoding="utf-8")
            package_commit = self._commit(source, "initial package")

            first_root = root / "first"
            stage_external_package(first_root, "cambonos-installer", source, package_commit)
            first = json.loads(
                (first_root / "packages/cambonos-installer/.cambonos-source.json").read_text()
            )
            self.assertEqual(first["commit"], package_commit)

            (source / "README.md").write_text("documentation v2\n", encoding="utf-8")
            documentation_commit = self._commit(source, "docs: update README")
            second_root = root / "second"
            stage_external_package(second_root, "cambonos-installer", source, documentation_commit)
            second = json.loads(
                (second_root / "packages/cambonos-installer/.cambonos-source.json").read_text()
            )
            self.assertEqual(second["commit"], package_commit)
            self.assertEqual(second["source_date_epoch"], first["source_date_epoch"])

            (source / "LICENSE").write_text("license v2\n", encoding="utf-8")
            license_commit = self._commit(source, "legal: update license")
            third_root = root / "third"
            stage_external_package(third_root, "cambonos-installer", source, license_commit)
            third = json.loads(
                (third_root / "packages/cambonos-installer/.cambonos-source.json").read_text()
            )
            self.assertEqual(third["commit"], license_commit)
            self.assertNotEqual(third["commit"], second["commit"])


if __name__ == "__main__":
    unittest.main()
