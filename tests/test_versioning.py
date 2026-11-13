"""Tests for CambonOS Package Versioning (CPV)."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.cambonos_lib.common import CambonosError
from scripts.cambonos_lib.manifest import validate_version_policy
from scripts.cambonos_lib.versioning import (
    format_arch_version,
    parse_pkgver,
    validate_package_version,
    validate_version_transition,
)


def fake_vercmp(old: str, new: str, _image: str) -> int:
    def key(value: str):
        _epoch, value = value.split(":", 1) if ":" in value else ("0", value)
        pkgver, pkgrel = value.rsplit("-", 1)
        return (int(_epoch), tuple(int(part) for part in pkgver.split(".")), int(pkgrel))
    return (key(old) > key(new)) - (key(old) < key(new))


class CPVFormatTests(unittest.TestCase):
    def test_accepts_numeric_triplet(self):
        self.assertEqual(parse_pkgver("1.2.3").pkgver, "1.2.3")
        validate_package_version("0.1.0", "1", "0")

    def test_rejects_non_cpv_pkgver(self):
        for value in ("1", "1.2", "1.2.3.4", "v1.2.3", "1.2.3-rc1", "01.2.3", "1.02.3"):
            with self.subTest(value=value), self.assertRaises(CambonosError):
                parse_pkgver(value)

    def test_rejects_invalid_pkgrel_and_epoch(self):
        for pkgrel in ("0", "-1", "01", "1.0"):
            with self.subTest(pkgrel=pkgrel), self.assertRaises(CambonosError):
                validate_package_version("1.2.3", pkgrel)
        with self.assertRaises(CambonosError):
            validate_package_version("1.2.3", "1", "-1")

    def test_formats_arch_version(self):
        self.assertEqual(format_arch_version("1.2.3", "4"), "1.2.3-4")
        self.assertEqual(format_arch_version("1.2.3", "4", "2"), "2:1.2.3-4")


    def test_all_repository_pkgbuilds_use_cpv(self):
        from pathlib import Path
        import re

        root = Path(__file__).resolve().parents[1]
        pkgbuils = sorted((root / "packages").glob("*/PKGBUILD"))
        self.assertEqual(len(pkgbuils), 13)
        for path in pkgbuils:
            text = path.read_text(encoding="utf-8")
            pkgver = re.search(r"(?m)^pkgver=([^\n#]+)", text)
            pkgrel = re.search(r"(?m)^pkgrel=([^\n#]+)", text)
            epoch = re.search(r"(?m)^epoch=([^\n#]+)", text)
            with self.subTest(package=path.parent.name):
                self.assertIsNotNone(pkgver)
                self.assertIsNotNone(pkgrel)
                validate_package_version(
                    pkgver.group(1).strip().strip("\\\"'"),
                    pkgrel.group(1).strip().strip("\\\"'"),
                    epoch.group(1).strip().strip("\\\"\'") if epoch else "0",
                )

class CPVTransitionTests(unittest.TestCase):
    def test_pkgrel_increments_with_same_pkgver(self):
        validate_version_transition("1.2.3-1", "1.2.3", "2", "0", "", fake_vercmp)

    def test_pkgver_change_accepts_positive_pkgrel(self):
        for pkgrel in ("1", "2", "9"):
            with self.subTest(pkgrel=pkgrel):
                validate_version_transition("1.2.3-9", "1.2.4", pkgrel, "0", "", fake_vercmp)
        validate_version_transition("0.7.0-1", "0.9.7", "2", "0", "", fake_vercmp)

    def test_rejects_downgrade(self):
        with self.assertRaises(CambonosError):
            validate_version_transition("1.2.3-2", "1.2.3", "1", "0", "", fake_vercmp)

    def test_epoch_is_part_of_arch_ordering(self):
        validate_version_transition("1:9.9.9-1", "0.1.0", "1", "2", "", fake_vercmp)



class CPVPublicationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.previous = {
            "channels": {
                "testing": {
                    "branch": "dev",
                    "packages": {
                        "cambonos-example": {
                            "version": "1.2.3-1",
                            "source_hash": "a" * 64,
                            "package_hash": "b" * 64,
                        }
                    },
                }
            }
        }
        self.current = {
            "cambonos-example": {
                "version": "1.2.3-1",
                "pkgver": "1.2.3",
                "pkgrel": "1",
                "epoch": "0",
                "source_hash": "a" * 64,
                "package_hash": "b" * 64,
            }
        }

    def test_identical_rebuild_is_allowed(self):
        with patch("scripts.cambonos_lib.manifest.compare_arch_versions", return_value=0):
            validate_version_policy(self.current, self.previous, "testing", "unused")

    def test_different_binary_with_same_version_is_rejected(self):
        self.current["cambonos-example"]["package_hash"] = "c" * 64
        with patch("scripts.cambonos_lib.manifest.compare_arch_versions", return_value=0):
            with self.assertRaisesRegex(CambonosError, "SHA-256 del binario ha cambiado"):
                validate_version_policy(self.current, self.previous, "testing", "unused")

    def test_source_change_with_same_version_is_rejected(self):
        self.current["cambonos-example"]["source_hash"] = "d" * 64
        with patch("scripts.cambonos_lib.manifest.compare_arch_versions", return_value=0):
            with self.assertRaisesRegex(CambonosError, "cambió el contenido fuente"):
                validate_version_policy(self.current, self.previous, "testing", "unused")

    def test_pkgver_change_accepts_pkgrel_greater_than_one(self):
        self.current["cambonos-example"].update(
            version="0.9.7-2", pkgver="0.9.7", pkgrel="2"
        )
        self.previous["channels"]["testing"]["packages"]["cambonos-example"]["version"] = "0.7.0-1"
        with patch("scripts.cambonos_lib.manifest.compare_arch_versions", return_value=-1):
            validate_version_policy(self.current, self.previous, "testing", "unused")


    def test_documentation_change_is_not_a_build_input_change(self):
        previous = {
            "channels": {"testing": {"packages": {
                "cambonos-example": {
                    "version": "1.2.3-1",
                    "source_hash": "a" * 64,
                    "build_input_hash": "b" * 64,
                    "package_hash": "c" * 64,
                }
            }}}
        }
        current = {
            "cambonos-example": {
                "version": "1.2.3-1", "pkgver": "1.2.3",
                "pkgrel": "1", "epoch": "0",
                "source_hash": "d" * 64,
                "build_input_hash": "b" * 64,
                "package_hash": "c" * 64,
            }
        }
        with patch("scripts.cambonos_lib.manifest.compare_arch_versions", return_value=0):
            validate_version_policy(current, previous, "testing", "unused")

    def test_changed_build_input_is_rejected_without_version_bump(self):
        previous = {
            "channels": {"testing": {"packages": {
                "cambonos-example": {
                    "version": "1.2.3-1",
                    "source_hash": "a" * 64,
                    "build_input_hash": "b" * 64,
                    "package_hash": "c" * 64,
                }
            }}}
        }
        current = {
            "cambonos-example": {
                "version": "1.2.3-1", "pkgver": "1.2.3",
                "pkgrel": "1", "epoch": "0",
                "source_hash": "a" * 64,
                "build_input_hash": "d" * 64,
                "package_hash": "c" * 64,
            }
        }
        with patch("scripts.cambonos_lib.manifest.compare_arch_versions", return_value=0):
            with self.assertRaisesRegex(CambonosError, "cambió el contenido fuente"):
                validate_version_policy(current, previous, "testing", "unused")


if __name__ == "__main__":
    unittest.main()
