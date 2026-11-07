import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.validation import (
    discover_packages, extract_array, extract_function, extract_scalar, validate_package,
    validate_all, dependency_name,
)
from cambonos_lib.common import CambonosError
from cambonos_lib.models import Package


class ValidationTests(unittest.TestCase):
    def test_static_parsers(self):
        text = """pkgname='sample'\npkgver=1.2\npkgrel=3\ndepends=('bash' 'coreutils>=9')\npackage() {\n  echo ok\n}\n"""
        self.assertEqual(extract_scalar(text, "pkgname"), "sample")
        self.assertEqual(extract_array(text, "depends"), ["bash", "coreutils>=9"])
        self.assertIn("echo ok", extract_function(text, "package"))

    def test_existing_packages_are_statically_valid(self):
        packages = discover_packages(ROOT)
        for name in (
            "cambonos-release", "cambonos-fastfetch", "cambonos-pacman", "cambonos-grub",
            "cambonos-plymouth",
        ):
            self.assertEqual(validate_package(packages[name]), [], name)

    def test_keyring_material_validation_is_consistent(self):
        packages = discover_packages(ROOT)
        keyring = packages["cambonos-keyring"]
        errors = validate_package(keyring)
        key_file = keyring.directory / "files" / "cambonos.gpg"
        if key_file.stat().st_size == 0:
            self.assertTrue(any("cambonos.gpg" in error for error in errors))
        else:
            self.assertEqual(errors, [])


    def _package(self, root, name="cambonos-sample", *, pkgver="1", pkgrel="1",
                 arch="any", epoch="0", depends="", makedepends="", checkdepends="",
                 check_function=""):
        directory = Path(root) / name
        (directory / "files").mkdir(parents=True)
        pkgb = (
            f"pkgname={name}\npkgver={pkgver}\npkgrel={pkgrel}\nepoch={epoch}\n"
            f"arch=('{arch}')\n"
            + (f"depends=({depends})\n" if depends else "")
            + (f"makedepends=({makedepends})\n" if makedepends else "")
            + (f"checkdepends=({checkdepends})\n" if checkdepends else "")
            + "package() { install -Dm644 \"$startdir/files/payload\" \"$pkgdir/usr/share/sample/payload\"; }\n"
            + check_function
        )
        (directory / "PKGBUILD").write_text(pkgb)
        (directory / "files" / "payload").write_text("payload")
        return Package(
            name=name, directory=directory, pkgver=pkgver, pkgrel=pkgrel,
            epoch=epoch, architecture=(arch,),
            depends=tuple(depends.replace("'", "").split()) if depends else (),
            makedepends=tuple(makedepends.replace("'", "").split()) if makedepends else (),
            checkdepends=tuple(checkdepends.replace("'", "").split()) if checkdepends else (),
        )

    def test_extract_array_handles_comments_and_quoted_spaces(self):
        text = "depends=('base package' # comment\n 'other>=2')\n"
        self.assertEqual(extract_array(text, "depends"), ["base package", "other>=2"])

    def test_extract_function_handles_nested_braces_and_quoted_braces(self):
        body = extract_function(
            'package() { echo "}"; if true; then echo ok; fi; }', "package"
        )
        self.assertIn("if true", body)
        self.assertIn('echo "}"', body)

    def test_extract_function_rejects_unclosed_function(self):
        with self.assertRaises(CambonosError):
            extract_function("package() { echo unfinished", "package")

    def test_dependency_name_strips_arch_version_operator(self):
        self.assertEqual(dependency_name("cambonos-base>=1:2.0-1"), "cambonos-base")
        self.assertEqual(dependency_name("bash"), "bash")
        self.assertIsNone(dependency_name(""))

    def test_validate_package_rejects_dynamic_version_and_invalid_epoch(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(temporary, pkgver="$pkgver", pkgrel="1", epoch="not-a-number")
            errors = validate_package(package)
            self.assertTrue(any("valores estáticos" in error for error in errors))
            self.assertTrue(any("epoch" in error for error in errors))

    def test_validate_package_rejects_unsupported_architecture(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(temporary, arch="aarch64")
            errors = validate_package(package)
            self.assertTrue(any("arch debe incluir" in error for error in errors))

    def test_validate_package_rejects_source_array_policy_violation(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(temporary)
            path = package.directory / "PKGBUILD"
            path.write_text(path.read_text() + "source=('https://example.invalid/file')\n")
            errors = validate_package(package)
            self.assertTrue(any("no declarar source=()" in error for error in errors))

    def test_validate_package_rejects_missing_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(temporary)
            path = package.directory / "PKGBUILD"
            path.write_text(path.read_text().replace("files/payload", "files/missing"))
            errors = validate_package(package)
            self.assertTrue(any("no existe el archivo fuente" in error for error in errors))

    def test_validate_external_package_allows_static_sources_at_checkout_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(temporary, name="cambonos-installer")
            directory = package.directory
            (directory / ".cambonos-source.json").write_text(
                '{"repository":"https://github.com/CambonOS/installer",'
                '"commit":"' + "a" * 40 + '","source_date_epoch":1}\n'
            )
            (directory / "payload").write_text("payload")
            pkgb = directory / "PKGBUILD"
            pkgb.write_text(
                pkgb.read_text().replace(
                    '"$startdir/files/payload"', '"$startdir/payload"'
                )
            )
            errors = validate_package(package)
            self.assertEqual(errors, [])

    def test_validate_external_package_rejects_sources_escaping_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(temporary, name="cambonos-installer")
            directory = package.directory
            (directory / ".cambonos-source.json").write_text(
                '{"repository":"https://github.com/CambonOS/installer",'
                '"commit":"' + "a" * 40 + '","source_date_epoch":1}\n'
            )
            pkgb = directory / "PKGBUILD"
            pkgb.write_text(
                pkgb.read_text().replace(
                    '"$startdir/files/payload"', '"$startdir/../outside"'
                )
            )
            errors = validate_package(package)
            self.assertTrue(any("referencia insegura" in error for error in errors))

    def test_validate_package_rejects_unsafe_install_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(temporary)
            path = package.directory / "PKGBUILD"
            path.write_text(path.read_text().replace("/usr/share/sample/payload", "/usr/../etc/payload"))
            errors = validate_package(package)
            self.assertTrue(any("destino inseguro" in error for error in errors))

    def test_validate_package_rejects_incomplete_alpm_hook(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(temporary)
            hook = package.directory / "files" / "broken.hook"
            hook.write_text("[Trigger]\nOperation = Install\n")
            errors = validate_package(package)
            self.assertTrue(any("hook" in error and "incompleto" in error for error in errors))

    def test_validate_all_rejects_missing_internal_dependency(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(temporary, depends="'cambonos-not-present>=1'")
            with self.assertRaisesRegex(CambonosError, "dependencia interna sin paquete"):
                validate_all({package.name: package})

    def test_validate_all_only_uses_checkdepends_when_check_function_exists(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = self._package(
                temporary, "cambonos-first", checkdepends="'cambonos-second'"
            )
            second = self._package(temporary, "cambonos-second")
            # No check() exists, so checkdepends must not introduce a build-order edge.
            validate_all({first.name: first, second.name: second})

    def test_validate_all_detects_checkdepends_cycle_when_check_exists(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = self._package(
                temporary, "cambonos-first", checkdepends="'cambonos-second'",
                check_function="check() { echo test; }\n",
            )
            second = self._package(
                temporary, "cambonos-second", makedepends="'cambonos-first'"
            )
            with self.assertRaisesRegex(CambonosError, "ciclo de dependencias"):
                validate_all({first.name: first, second.name: second})


if __name__ == "__main__":
    unittest.main()
