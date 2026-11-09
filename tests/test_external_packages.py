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
    def _checkout(
        self, root, package_name="cambonos-installer",
        repository="https://github.com/CambonOS/cambonos-installer.git",
    ):
        source = root / "installer-source"
        source.mkdir()
        (source / "files").mkdir()
        (source / "PKGBUILD").write_text(
            f"pkgname={package_name}\npkgver=1\npkgrel=1\n"
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
             repository], check=True
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
            self.assertEqual(metadata["repository"], "https://github.com/CambonOS/cambonos-installer")
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

    def test_stages_system_root_symlinks_in_mkiso_airootfs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, _commit = self._checkout(
                root, "cambonos-mkiso",
                "https://github.com/CambonOS/cambonos-mkiso.git",
            )
            system_dir = source / "files/profile/airootfs/etc/systemd/system"
            wants_dir = system_dir / "multi-user.target.wants"
            wants_dir.mkdir(parents=True)
            (system_dir / "systemd-firstboot.service").symlink_to("/dev/null")
            (wants_dir / "NetworkManager.service").symlink_to(
                "/usr/lib/systemd/system/NetworkManager.service"
            )
            (wants_dir / "pacman-init.service").symlink_to("../pacman-init.service")
            subprocess.run(["git", "-C", str(source), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(source), "commit", "-qm", "add airootfs links"], check=True
            )
            commit = subprocess.run(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                check=True, text=True, capture_output=True,
            ).stdout.strip()

            staged = stage_external_package(root / "central", "cambonos-mkiso", source, commit)

            staged_system_dir = staged / "files/profile/airootfs/etc/systemd/system"
            self.assertEqual((staged_system_dir / "systemd-firstboot.service").readlink(), Path("/dev/null"))
            self.assertEqual(
                (staged_system_dir / "multi-user.target.wants/NetworkManager.service").readlink(),
                Path("/usr/lib/systemd/system/NetworkManager.service"),
            )
            self.assertEqual(
                (staged_system_dir / "multi-user.target.wants/pacman-init.service").readlink(),
                Path("../pacman-init.service"),
            )

    def test_rejects_relative_symlink_escaping_airootfs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, _commit = self._checkout(
                root, "cambonos-mkiso",
                "https://github.com/CambonOS/cambonos-mkiso.git",
            )
            system_dir = source / "files/profile/airootfs/etc/systemd/system"
            system_dir.mkdir(parents=True)
            (system_dir / "escape").symlink_to("../../../../PKGBUILD")
            subprocess.run(["git", "-C", str(source), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(source), "commit", "-qm", "add escaping airootfs link"],
                check=True,
            )
            commit = subprocess.run(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                check=True, text=True, capture_output=True,
            ).stdout.strip()

            with self.assertRaisesRegex(CambonosError, "escapa de airootfs"):
                stage_external_package(root / "central", "cambonos-mkiso", source, commit)


if __name__ == "__main__":
    unittest.main()