from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.cambonos_lib.models import Package
from scripts.cambonos_lib.common import CambonosError
from scripts.cambonos_lib.planner import create_build_plan, package_input_hash


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
        self.assertEqual(plan["summary"], {"build": 2, "reuse_candidates": 0, "removed": 0})
        self.assertEqual(plan["mode"], "plan-only")

    def test_identical_fingerprints_are_reused(self):
        initial = create_build_plan(self.packages, "testing", "arch-image")
        previous = {"packages": {
            name: {
                "build_fingerprint": item["build_fingerprint"],
                "package_hash": "a" * 64,
                "package_file": f"{name}-1.0.0-1-any.pkg.tar.zst",
                "version": "1.0.0-1",
                "architecture": "any",
                "signature_file": f"{name}-1.0.0-1-any.pkg.tar.zst.sig",
                "signature_hash": "b" * 64,
            } for name, item in initial["packages"].items()
        }}
        plan = create_build_plan(self.packages, "testing", "arch-image", previous)
        self.assertEqual(plan["summary"], {"build": 0, "reuse_candidates": 2, "removed": 0})

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
                "package_hash": "a" * 64,
                "package_file": f"{name}-1.0.0-1-any.pkg.tar.zst",
                "version": "1.0.0-1",
                "architecture": "any",
                "signature_file": f"{name}-1.0.0-1-any.pkg.tar.zst.sig",
                "signature_hash": "b" * 64,
            } for name, item in first["packages"].items()
        }}
        (self.dep.directory / "files/payload").write_text("changed")
        second = create_build_plan(self.packages, "testing", "arch-image", previous)
        self.assertEqual(second["packages"]["cambonos-dep"]["action"], "build")
        self.assertEqual(second["packages"]["cambonos-app"]["action"], "build")

    def test_systemd_wants_symlink_is_included_in_fingerprint(self):
        systemd = self.app.directory / "files/profile/airootfs/etc/systemd/system"
        wants = systemd / "multi-user.target.wants"
        wants.mkdir(parents=True)
        (systemd / "pacman-init.service").write_text("[Service]\n")
        link = wants / "pacman-init.service"
        link.symlink_to("../pacman-init.service")

        first = package_input_hash(self.app)
        link.unlink()
        link.symlink_to("../../system/pacman-init.service")

        self.assertNotEqual(first, package_input_hash(self.app))

    def test_internal_directory_symlink_is_hashed_without_traversal(self):
        target = self.app.directory / "files/systemd"
        target.mkdir()
        (target / "unit.service").write_text("[Service]\n")
        (self.app.directory / "files/systemd-link").symlink_to("systemd", target_is_directory=True)

        self.assertEqual(len(package_input_hash(self.app)), 64)

    def test_relative_symlink_escaping_files_is_rejected(self):
        (self.app.directory / "README.md").write_text("not a build payload")
        (self.app.directory / "files/outside.service").symlink_to("../README.md")

        with self.assertRaisesRegex(CambonosError, "fuera de files"):
            package_input_hash(self.app)

    def test_absolute_rootfs_symlinks_are_hashed_without_host_resolution(self):
        wants = self.app.directory / "files/systemd/multi-user.target.wants"
        wants.mkdir(parents=True)
        (wants / "NetworkManager.service").symlink_to(
            "/usr/lib/systemd/system/NetworkManager.service"
        )
        (self.app.directory / "files/systemd/systemd-firstboot.service").symlink_to(
            "/dev/null"
        )

        first = package_input_hash(self.app)
        (wants / "NetworkManager.service").unlink()
        (wants / "NetworkManager.service").symlink_to(
            "/usr/lib/systemd/system/NetworkManager-wait-online.service"
        )
        self.assertNotEqual(first, package_input_hash(self.app))

    def test_relative_symlink_chain_may_end_at_absolute_rootfs_target(self):
        systemd = self.app.directory / "files/systemd"
        systemd.mkdir()
        (systemd / "real.service").symlink_to("/usr/lib/systemd/system/real.service")
        (systemd / "alias.service").symlink_to("real.service")

        self.assertEqual(len(package_input_hash(self.app)), 64)

    def test_broken_symlink_is_rejected(self):
        (self.app.directory / "files/broken.service").symlink_to("missing.service")

        with self.assertRaisesRegex(CambonosError, "roto o cíclico"):
            package_input_hash(self.app)

    def test_symlink_cycle_is_rejected(self):
        first = self.app.directory / "files/first"
        second = self.app.directory / "files/second"
        first.symlink_to("second")
        second.symlink_to("first")

        with self.assertRaisesRegex(CambonosError, "roto o cíclico"):
            package_input_hash(self.app)

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
