import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cambonos_lib"))

from stage_external_packages import stage_external_package
from cambonos_lib.common import CambonosError
from cambonos_lib.models import Package
from cambonos_lib.validation import validate_package


class ExternalPackageStagingTests(unittest.TestCase):
    def _checkout(self, root):
        source = root / "installer-source"
        source.mkdir()
        (source / "files").mkdir()
        (source / "PKGBUILD").write_text(
            "pkgname=cambonos-installer\npkgver=1\npkgrel=1\n"
            "arch=('any')\n"
            'package() { install -Dm644 "$startdir/payload" '
            '"$pkgdir/usr/share/sample/payload"; }\n'
        )
        (source / "payload").write_text("payload")
        subprocess.run(["git", "init", "-q", str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(source), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(
            ["git", "-C", str(source), "remote", "add", "origin",
             "https://github.com/CambonOS/installer.git"], check=True
        )
        subprocess.run(["git", "-C", str(source), "add", "."], check=True)
        subprocess.run(["git", "-C", str(source), "commit", "-qm", "package source"], check=True)
        commit = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            check=True, text=True, capture_output=True,
        ).stdout.strip()
        return source, commit

    def test_stages_clean_verified_checkout_and_records_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, commit = self._checkout(root)
            destination = stage_external_package(root / "central", "cambonos-installer", source, commit)
            metadata = json.loads((destination / ".cambonos-source.json").read_text())
            self.assertEqual(metadata["commit"], commit)
            self.assertEqual(metadata["repository"], "https://github.com/CambonOS/installer")
            self.assertEqual((destination / "payload").read_text(), "payload")
            self.assertFalse((destination / ".git").exists())
            package = Package(
                name="cambonos-installer", directory=destination,
                pkgver="1", pkgrel="1", architecture=("any",),
            )
            self.assertEqual(validate_package(package), [])

    def test_rejects_mismatched_commit_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, commit = self._checkout(root)
            with self.assertRaisesRegex(CambonosError, "checkout externo incorrecto"):
                stage_external_package(root / "central", "cambonos-installer", source, "0" * 40)
            staged = stage_external_package(root / "central", "cambonos-installer", source, commit)
            with self.assertRaisesRegex(CambonosError, "ya existe"):
                stage_external_package(root / "central", "cambonos-installer", source, commit)

    def test_rejects_symlink_escaping_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, _commit = self._checkout(root)
            (source / "escape").symlink_to(root / "outside")
            subprocess.run(["git", "-C", str(source), "add", "escape"], check=True)
            subprocess.run(["git", "-C", str(source), "commit", "-qm", "add symlink"], check=True)
            commit = subprocess.run(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                check=True, text=True, capture_output=True,
            ).stdout.strip()
            with self.assertRaisesRegex(CambonosError, "symlink externo que escapa"):
                stage_external_package(root / "central", "cambonos-installer", source, commit)


if __name__ == "__main__":
    unittest.main()