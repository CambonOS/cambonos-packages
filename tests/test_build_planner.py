from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.cambonos_lib.models import Package
from scripts.cambonos_lib.planner import create_build_plan


def make_package(root: Path, name: str, makedepends: str = "") -> Package:
    directory = root / name
    (directory / "files").mkdir(parents=True)
    (directory / "PKGBUILD").write_text(
        f"pkgname={name}\npkgver=1.0.0\npkgrel=1\narch=('any')\n"
        f"makedepends=({makedepends})\npackage() {{ :; }}\n",
        encoding="utf-8",
    )
    return Package(
        name=name, directory=directory, pkgver="1.0.0", pkgrel="1",
        architecture=("any",), makedepends=tuple(
            value.strip("'\\\"") for value in makedepends.split() if value
        ),
    )


class BuildPlannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dep = make_package(self.root, "cambonos-dep")
        self.app = make_package(self.root, "cambonos-app", "'cambonos-dep'")
        self.packages = {p.name: p for p in (self.dep, self.app)}

    def tearDown(self):
        self.temp.cleanup()

    def test_first_plan_builds_everything(self):
        plan = create_build_plan(self.packages, "testing", "arch-image")
        self.assertEqual(plan["summary"], {"build": 2, "reuse_candidates": 0})
        self.assertEqual(plan["mode"], "plan-only")

    def test_identical_fingerprints_are_reused(self):
        initial = create_build_plan(self.packages, "testing", "arch-image")
        previous = {"packages": {
            name: {
                "build_fingerprint": item["build_fingerprint"],
                "package_hash": "a" * 64,
                "package_file": f"{name}-1.0.0-1-any.pkg.tar.zst",
                "version": "1.0.0-1",
            } for name, item in initial["packages"].items()
        }}
        plan = create_build_plan(self.packages, "testing", "arch-image", previous)
        self.assertEqual(plan["summary"], {"build": 0, "reuse_candidates": 2})

    def test_package_readme_does_not_change_fingerprint(self):
        first = create_build_plan(self.packages, "testing", "arch-image")
        (self.app.directory / "README.md").write_text("documentation only")
        second = create_build_plan(self.packages, "testing", "arch-image")
        self.assertEqual(
            first["packages"]["cambonos-app"]["build_fingerprint"],
            second["packages"]["cambonos-app"]["build_fingerprint"],
        )

    def test_payload_change_rebuilds_package_and_internal_dependents(self):
        first = create_build_plan(self.packages, "testing", "arch-image")
        previous = {"packages": {
            name: {
                "build_fingerprint": item["build_fingerprint"],
                "package_hash": "a" * 64, "package_file": f"{name}.pkg.tar.zst",
                "version": "1.0.0-1",
            } for name, item in first["packages"].items()
        }}
        (self.dep.directory / "files/payload").write_text("changed")
        second = create_build_plan(self.packages, "testing", "arch-image", previous)
        self.assertEqual(second["packages"]["cambonos-dep"]["action"], "build")
        self.assertEqual(second["packages"]["cambonos-app"]["action"], "build")

    def test_channel_profiles_are_distinct_for_pacman_only(self):
        pacman = make_package(self.root, "cambonos-pacman")
        (pacman.directory / "files/cambonos.conf").write_text("[cambonos]\\n")
        packages = {"cambonos-pacman": pacman}
        testing = create_build_plan(packages, "testing", "arch-image")
        stable = create_build_plan(packages, "stable", "arch-image")
        self.assertNotEqual(
            testing["packages"]["cambonos-pacman"]["build_fingerprint"],
            stable["packages"]["cambonos-pacman"]["build_fingerprint"],
        )
        common_testing = create_build_plan({"cambonos-dep": self.dep}, "testing", "arch-image")
        common_stable = create_build_plan({"cambonos-dep": self.dep}, "stable", "arch-image")
        self.assertEqual(
            common_testing["packages"]["cambonos-dep"]["build_fingerprint"],
            common_stable["packages"]["cambonos-dep"]["build_fingerprint"],
        )


if __name__ == "__main__":
    unittest.main()
