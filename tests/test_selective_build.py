from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cambonos_lib.build import build_channel
from scripts.cambonos_lib.models import Package
from scripts.cambonos_lib.planner import create_build_plan
from scripts.cambonos_lib.manifest import verify_build_manifest


def package(root: Path, name: str, makedepends: tuple[str, ...] = ()) -> Package:
    directory = root / name
    (directory / "files").mkdir(parents=True)
    (directory / "PKGBUILD").write_text(
        f"pkgname={name}\npkgver=1.0.0\npkgrel=1\narch=('any')\n"
        + (f"makedepends=({' '.join(makedepends)})\n" if makedepends else "")
        + "package() { :; }\n",
        encoding="utf-8",
    )
    return Package(
        name=name, directory=directory, pkgver="1.0.0", pkgrel="1",
        architecture=("any",), makedepends=makedepends,
    )


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SelectiveBuildTests(unittest.TestCase):
    def test_reuses_verified_dependency_and_builds_changed_dependent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dep = package(root / "sources", "cambonos-dep")
            app = package(root / "sources", "cambonos-app", ("cambonos-dep",))
            packages = {dep.name: dep, app.name: app}
            old_plan = create_build_plan(packages, "testing", "arch-image")

            recovered_dir = root / "recovered"
            recovered_dir.mkdir()
            old_records = {}
            recovered = {}
            for name, item in old_plan["packages"].items():
                filename = f"{name}-1.0.0-1-any.pkg.tar.zst"
                archive = recovered_dir / filename
                signature = recovered_dir / (filename + ".sig")
                archive.write_bytes((name + "-old-binary").encode())
                signature.write_bytes((name + "-old-signature").encode())
                old_records[name] = {
                    "version": "1.0.0-1", "pkgver": "1.0.0", "pkgrel": "1",
                    "epoch": "0", "architecture": "any",
                    "package_file": filename, "package_hash": sha(archive),
                    "signature_file": filename + ".sig", "signature_hash": sha(signature),
                    "source_hash": "e" * 64, "source_date_epoch": 111,
                    "build_fingerprint": item["build_fingerprint"],
                    "build_input_hash": item["build_input_hash"],
                    "build_recipe_hash": item["build_recipe_hash"],
                    "channel_profile_hash": item["channel_profile_hash"],
                    "dependency_fingerprints": item["dependency_fingerprints"],
                }
                recovered[name] = (archive, signature)

            (app.directory / "files/payload").write_text("changed app input")
            previous = {"channels": {"testing": {"commit": "d" * 40, "packages": old_records}}}
            (root / "manifest.json").write_text("{}")
            (root / "manifest.json.sig").write_bytes(b"manifest-signature")
            output = root / "output"

            observed_internal = []

            def fake_build_one(pkg, channel, image, pkg_output, internal, source_epoch):
                observed_internal.extend((name, path.name) for name, path in internal)
                pkg_output.mkdir(parents=True, exist_ok=True)
                archive = pkg_output / f"{pkg.name}-{pkg.pkgver}-{pkg.pkgrel}-any.pkg.tar.zst"
                archive.write_bytes((pkg.name + "-new-binary").encode())
                (pkg_output / "build-environment.txt").write_text("fake build environment")
                return archive, {
                    "version": f"{pkg.pkgver}-{pkg.pkgrel}",
                    "pkgver": pkg.pkgver, "pkgrel": pkg.pkgrel, "epoch": pkg.epoch,
                    "architecture": "any", "source_hash": "c" * 64,
                    "source_date_epoch": source_epoch,
                    "package_file": archive.name, "package_hash": sha(archive),
                }

            with (
                patch(
                    "scripts.cambonos_lib.artifacts.validate_recovered_artifacts_for_build",
                    return_value=(previous, recovered),
                ),
                patch("scripts.cambonos_lib.build._package_source_date_epoch", return_value=123),
                patch("scripts.cambonos_lib.build._build_one", side_effect=fake_build_one) as build_one,
            ):
                build_channel(
                    packages, "testing", "dev", "a" * 40, "arch-image", output,
                    previous_manifest_path=root / "manifest.json",
                    previous_manifest_signature_path=root / "manifest.json.sig",
                    keyring_public_key_path=root / "keyring.gpg",
                    keyring_trusted_path=root / "trusted",
                    recovered_dir=recovered_dir,
                )

            self.assertEqual(build_one.call_count, 1)
            self.assertEqual(build_one.call_args.args[0].name, "cambonos-app")
            self.assertEqual(observed_internal, [
                ("cambonos-dep", "cambonos-dep-1.0.0-1-any.pkg.tar.zst")
            ])
            report = json.loads((output / "build-selection-report.json").read_text())
            self.assertEqual(report["summary"], {"total": 2, "built": 1, "reused": 1, "removed": 0})
            self.assertEqual(report["packages"]["cambonos-dep"]["action"], "reuse")
            self.assertEqual(report["packages"]["cambonos-app"]["action"], "build")
            self.assertTrue((output / "packages/cambonos-dep-1.0.0-1-any.pkg.tar.zst.sig").is_file())
            manifest = verify_build_manifest(output / "build-manifest.json", output / "packages")
            self.assertTrue(manifest["packages"]["cambonos-dep"]["reused_from_publication"])
            self.assertEqual(manifest["packages"]["cambonos-dep"]["source_hash"], "e" * 64)
            self.assertEqual(manifest["packages"]["cambonos-dep"]["reused_from_commit"], "d" * 40)
            self.assertFalse(manifest["packages"]["cambonos-app"]["reused_from_publication"])

    def test_without_recovery_falls_back_to_full_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            one = package(root / "sources", "cambonos-one")
            output = root / "output"

            def fake_build_one(pkg, channel, image, pkg_output, internal, source_epoch):
                pkg_output.mkdir(parents=True, exist_ok=True)
                archive = pkg_output / f"{pkg.name}-1.0.0-1-any.pkg.tar.zst"
                archive.write_bytes(b"fresh")
                (pkg_output / "build-environment.txt").write_text("env")
                return archive, {
                    "version": "1.0.0-1", "pkgver": "1.0.0", "pkgrel": "1",
                    "epoch": "0", "architecture": "any", "source_hash": "d" * 64,
                    "source_date_epoch": source_epoch, "package_file": archive.name,
                    "package_hash": sha(archive),
                }

            with (
                patch("scripts.cambonos_lib.build._package_source_date_epoch", return_value=123),
                patch("scripts.cambonos_lib.build._build_one", side_effect=fake_build_one) as build_one,
            ):
                build_channel(
                    {one.name: one}, "testing", "dev", "b" * 40, "arch-image", output
                )
            self.assertEqual(build_one.call_count, 1)
            report = json.loads((output / "build-selection-report.json").read_text())
            self.assertEqual(report["mode"], "full-build")
            self.assertEqual(report["summary"], {"total": 1, "built": 1, "reused": 0, "removed": 0})


    def test_unchanged_package_is_reused_without_invoking_builder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            one = package(root / "sources", "cambonos-one")
            packages = {one.name: one}
            plan = create_build_plan(packages, "testing", "arch-image")
            recovered_dir = root / "recovered"
            recovered_dir.mkdir()
            filename = "cambonos-one-1.0.0-1-any.pkg.tar.zst"
            archive = recovered_dir / filename
            signature = recovered_dir / (filename + ".sig")
            archive.write_bytes(b"published-package")
            signature.write_bytes(b"published-signature")
            digest = lambda path: sha(path)
            old_record = {
                "version": "1.0.0-1", "pkgver": "1.0.0", "pkgrel": "1",
                "epoch": "0", "architecture": "any",
                "package_file": filename, "package_hash": digest(archive),
                "signature_file": filename + ".sig", "signature_hash": digest(signature),
                "source_hash": "e" * 64, "source_date_epoch": 111,
                "build_fingerprint": plan["packages"][one.name]["build_fingerprint"],
                "build_input_hash": plan["packages"][one.name]["build_input_hash"],
                "build_recipe_hash": plan["packages"][one.name]["build_recipe_hash"],
                "channel_profile_hash": plan["packages"][one.name]["channel_profile_hash"],
                "dependency_fingerprints": {},
            }
            previous = {"channels": {"testing": {"commit": "d" * 40, "packages": {one.name: old_record}}}}
            (root / "manifest.json").write_text("{}")
            (root / "manifest.json.sig").write_bytes(b"manifest-signature")
            output = root / "output"
            with (
                patch(
                    "scripts.cambonos_lib.artifacts.validate_recovered_artifacts_for_build",
                    return_value=(previous, {one.name: (archive, signature)}),
                ),
                patch("scripts.cambonos_lib.build._package_source_date_epoch", return_value=123),
                patch("scripts.cambonos_lib.build._build_one") as build_one,
            ):
                build_channel(
                    packages, "testing", "dev", "c" * 40, "arch-image", output,
                    previous_manifest_path=root / "manifest.json",
                    previous_manifest_signature_path=root / "manifest.json.sig",
                    keyring_public_key_path=root / "keyring.gpg",
                    keyring_trusted_path=root / "trusted",
                    recovered_dir=recovered_dir,
                )
            build_one.assert_not_called()
            report = json.loads((output / "build-selection-report.json").read_text())
            self.assertEqual(report["summary"], {
                "total": 1, "built": 0, "reused": 1, "removed": 0,
            })


if __name__ == "__main__":
    unittest.main()
