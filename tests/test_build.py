import sys
import unittest
from unittest.mock import patch
import tempfile
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.build import build_order, _package_source_date_epoch, _build_one
from cambonos_lib.common import CambonosError, sha256_directory, sha256_file
from cambonos_lib.models import Package


def package(name, depends=(), makedepends=(), checkdepends=()):
    return Package(
        name=name, directory=ROOT / "packages" / name,
        pkgver="1", pkgrel="1", depends=depends,
        makedepends=makedepends, checkdepends=checkdepends,
    )


class BuildGraphTests(unittest.TestCase):
    def test_runtime_dependency_does_not_force_build_order(self):
        packages = {
            "cambonos-fastfetch": package("cambonos-fastfetch", depends=("cambonos-release",)),
            "cambonos-release": package("cambonos-release"),
        }
        self.assertEqual(build_order(packages), ["cambonos-fastfetch", "cambonos-release"])

    def test_internal_makedepends_is_built_first(self):
        packages = {
            "cambonos-addon": package("cambonos-addon", makedepends=("cambonos-core",)),
            "cambonos-core": package("cambonos-core"),
        }
        self.assertEqual(build_order(packages), ["cambonos-core", "cambonos-addon"])

    def test_source_date_epoch_uses_last_package_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            package_dir = repo / "packages" / "cambonos-sample"
            package_dir.mkdir(parents=True)
            (package_dir / "PKGBUILD").write_text("pkgname=cambonos-sample\\n")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "CambonOS Test"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "add package"], check=True)
            commit = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                check=True, text=True, capture_output=True,
            ).stdout.strip()
            expected = int(subprocess.run(
                ["git", "-C", str(repo), "log", "-1", "--format=%at", commit,
                 "--", "packages/cambonos-sample"],
                check=True, text=True, capture_output=True,
            ).stdout.strip())
            pkg = Package(
                name="cambonos-sample", directory=package_dir,
                pkgver="1", pkgrel="1",
            )
            self.assertEqual(_package_source_date_epoch(pkg, commit), expected)

    def test_source_date_epoch_uses_external_commit_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            package_dir = Path(temporary) / "packages" / "cambonos-installer"
            package_dir.mkdir(parents=True)
            (package_dir / ".cambonos-source.json").write_text(
                '{"source_date_epoch":1234567890}\n'
            )
            pkg = Package(
                name="cambonos-installer", directory=package_dir,
                pkgver="1", pkgrel="1",
            )
            self.assertEqual(_package_source_date_epoch(pkg, "a" * 40), 1234567890)

    def test_build_dependency_cycle_fails(self):
        packages = {
            "cambonos-a": package("cambonos-a", makedepends=("cambonos-b",)),
            "cambonos-b": package("cambonos-b", makedepends=("cambonos-a",)),
        }
        with self.assertRaises(CambonosError):
            build_order(packages)

    def test_checkdepends_only_affects_order_when_check_function_exists(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_dir = root / "first"; second_dir = root / "second"
            first_dir.mkdir(); second_dir.mkdir()
            (first_dir / "PKGBUILD").write_text("pkgname=cambonos-first\n")
            (second_dir / "PKGBUILD").write_text("pkgname=cambonos-second\n")
            first = Package(name="cambonos-first", directory=first_dir, pkgver="1", pkgrel="1",
                            checkdepends=("cambonos-second",))
            second = Package(name="cambonos-second", directory=second_dir, pkgver="1", pkgrel="1")
            self.assertEqual(build_order({first.name: first, second.name: second}),
                             ["cambonos-first", "cambonos-second"])
            (first_dir / "PKGBUILD").write_text(
                "pkgname=cambonos-first\ncheck() { echo test; }\n"
            )
            self.assertEqual(build_order({first.name: first, second.name: second}),
                             ["cambonos-second", "cambonos-first"])

    def test_build_order_rejects_missing_internal_build_dependency(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary); (directory / "PKGBUILD").write_text("pkgname=cambonos-addon\n")
            addon = Package(name="cambonos-addon", directory=directory, pkgver="1", pkgrel="1",
                            makedepends=("cambonos-missing>=1",))
            with self.assertRaisesRegex(CambonosError, "dependencia interna de construcción inexistente"):
                build_order({addon.name: addon})

    @patch("cambonos_lib.build.require_commands")
    @patch("cambonos_lib.build.run_command")
    def test_build_one_uses_isolated_input_and_records_hashes(self, run, _require):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_dir = root / "cambonos-sample"
            (package_dir / "files").mkdir(parents=True)
            (package_dir / "PKGBUILD").write_text(
                "pkgname=cambonos-sample\npkgver=1.2\npkgrel=3\n"
                "package() { :; }\ncheck() { :; }\n"
            )
            (package_dir / ".cambonos-source.json").write_text(
                '{"repository":"https://github.com/CambonOS/installer",'
                '"commit":"' + "a" * 40 + '","source_date_epoch":123}\n'
            )
            output = root / "out"
            internal = root / "internal.pkg.tar.zst"
            internal.write_bytes(b"dependency")
            package_obj = Package(
                name="cambonos-sample", directory=package_dir,
                pkgver="1.2", pkgrel="3", architecture=("any",),
            )

            def fake_docker(command):
                self.assertIn("CHECK_PRESENT=1", command)
                self.assertIn("EXPECTED_VERSION=1.2-3", command)
                self.assertIn("/input:ro", " ".join(command))
                (output / "sample-1.2-3-any.pkg.tar.zst").write_bytes(b"built archive")
                (output / "build-environment.txt").write_text("Arch build environment")
            run.side_effect = fake_docker
            archive, record = _build_one(
                package_obj, "arch-image", output,
                [("cambonos-dependency", internal)], 123456,
            )
            self.assertTrue(archive.is_file())
            self.assertEqual(record["source_hash"], sha256_directory(package_dir))
            self.assertEqual(record["package_hash"], sha256_file(archive))
            self.assertEqual(record["source_commit"], "a" * 40)
            self.assertTrue((output / ".internal" / internal.name).is_file())

    @patch("cambonos_lib.build.require_commands")
    @patch("cambonos_lib.build.run_command")
    def test_build_one_rejects_missing_environment_record(self, run, _require):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); package_dir = root / "pkg"; package_dir.mkdir()
            (package_dir / "PKGBUILD").write_text("pkgname=cambonos-sample\npackage() { :; }\n")
            output = root / "out"
            package_obj = Package(name="cambonos-sample", directory=package_dir,
                                  pkgver="1", pkgrel="1")
            def fake_docker(_command):
                (output / "sample-1-1-any.pkg.tar.zst").write_bytes(b"archive")
            run.side_effect = fake_docker
            with self.assertRaisesRegex(CambonosError, "falta build-environment.txt"):
                _build_one(package_obj, "image", output, [], 1)


if __name__ == "__main__":
    unittest.main()
