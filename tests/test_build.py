import sys
import unittest
import tempfile
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.build import build_order, _package_source_date_epoch
from cambonos_lib.common import CambonosError
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

    def test_build_dependency_cycle_fails(self):
        packages = {
            "cambonos-a": package("cambonos-a", makedepends=("cambonos-b",)),
            "cambonos-b": package("cambonos-b", makedepends=("cambonos-a",)),
        }
        with self.assertRaises(CambonosError):
            build_order(packages)


if __name__ == "__main__":
    unittest.main()
