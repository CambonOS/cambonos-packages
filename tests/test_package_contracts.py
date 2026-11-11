"""Behavioral contracts for the packages shipped by CambonOS.

These tests describe the package's purpose and required deliverables. They must
not freeze implementation details such as helper names, hook filenames, shell
block markers, or the exact way a PKGBUILD installs a file.
"""
from __future__ import annotations

import configparser
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"

# Required deliverables are expressed as package capabilities, not as a full
# inventory of implementation files. Optional integrations remain optional.
REQUIRED_PAYLOADS = {
    "cambonos-branding": (
        "files/cambonos-icon.svg", "files/cambonos-text.svg",
        "files/cambonos-icon.png", "files/cambonos-text.png",
    ),
    "cambonos-fastfetch": (
        "files/cambonos/fastfetch/config.jsonc",
        "files/cambonos/fastfetch/logo.txt",
    ),
    "cambonos-grub": (
        "files/defaults/60-cambonos.cfg",
        "files/themes/CambonOS/theme.txt",
    ),
    "cambonos-gtk-theme": (
        "files/src/palette.json",
        "files/themes/CambonOS-dark/index.theme",
        "files/themes/CambonOS-dark/gtk-3.0/gtk.css",
        "files/themes/CambonOS-dark/gtk-4.0/gtk.css",
    ),
    "cambonos-keyring": (
        "files/cambonos.gpg", "files/cambonos-trusted", "files/cambonos-revoked",
    ),
    "cambonos-lightdm": (
        "files/lightdm/50-cambonos.conf",
        "files/slick-greeter/slick-greeter.conf",
    ),
    "cambonos-pacman": (
        "files/cambonos.conf", "files/cambonos-options.conf",
    ),
    "cambonos-plymouth": (
        "files/themes/cambonos/cambonos.plymouth",
        "files/themes/cambonos/cambonos.script",
        "files/mkinitcpio/90-cambonos-plymouth.conf",
    ),
    "cambonos-release": (
        "files/cambonos/os-release", "files/cambonos/lsb-release",
    ),
    "cambonos-shell-prompt": (
        "files/starship.toml", "files/bash/cambonos-shell-prompt.bash",
        "files/fish/cambonos-shell-prompt.fish",
    ),
    "cambonos-zsh": (
        "files/etc/skel/.zshrc", "files/zsh/conf.d/10-completion.zsh",
    ),
    "cambonos-base": (),
}


class PackageContractTests(unittest.TestCase):
    def package_dirs(self):
        return sorted(p for p in PACKAGES.iterdir() if p.is_dir() and (p / "PKGBUILD").is_file())

    def test_every_local_package_has_basic_metadata_and_documentation(self):
        dirs = self.package_dirs()
        self.assertTrue(dirs, "No se han descubierto paquetes")
        for package in dirs:
            with self.subTest(package=package.name):
                self.assertTrue((package / "README.md").is_file(), "Falta README del paquete")
                text = (package / "PKGBUILD").read_text(encoding="utf-8")
                for field in ("pkgname", "pkgver", "pkgrel", "arch"):
                    self.assertRegex(text, rf"(?m)^{field}=", f"Falta {field} en PKGBUILD")
                self.assertRegex(text, rf"(?m)^pkgname={re.escape(package.name)}$")

    def test_each_package_contains_the_deliverables_for_its_purpose(self):
        for name, paths in REQUIRED_PAYLOADS.items():
            package = PACKAGES / name
            with self.subTest(package=name):
                self.assertTrue((package / "PKGBUILD").is_file())
                for relative in paths:
                    self.assertTrue((package / relative).is_file(), f"Falta {relative}")

    def test_base_metapackage_depends_on_all_core_components(self):
        text = (PACKAGES / "cambonos-base" / "PKGBUILD").read_text(encoding="utf-8")
        # A metapackage must install the core experience through dependencies;
        # do not prescribe how those dependencies are declared in Bash.
        for name in (
            "cambonos-keyring", "cambonos-pacman", "cambonos-release",
            "cambonos-branding", "cambonos-fastfetch",
            "cambonos-shell-prompt", "cambonos-zsh",
        ):
            self.assertIn(name, text)

    def test_metapackage_does_not_ship_payload(self):
        package = PACKAGES / "cambonos-base"
        files = [p for p in package.rglob("*") if p.is_file() and p.name not in {"PKGBUILD", "README.md"}]
        self.assertEqual(files, [], "cambonos-base debe seguir siendo un metapaquete")

    def test_keyring_contains_public_trust_material(self):
        keyring = PACKAGES / "cambonos-keyring" / "files"
        for name in ("cambonos.gpg", "cambonos-trusted", "cambonos-revoked"):
            self.assertTrue((keyring / name).is_file())
        self.assertGreater((keyring / "cambonos.gpg").stat().st_size, 0)

    def test_repository_configuration_requires_signature_verification(self):
        package = PACKAGES / "cambonos-pacman"
        configs = "\n".join(p.read_text(encoding="utf-8") for p in (package / "files").glob("*.conf"))
        self.assertRegex(configs, r"(?im)^\s*SigLevel\s*=.*(Required|PackageRequired)")

    def test_release_metadata_identifies_cambonos(self):
        release = PACKAGES / "cambonos-release" / "files/cambonos/os-release"
        content = release.read_text(encoding="utf-8")
        self.assertRegex(content, r"(?m)^ID=cambonos$")
        self.assertRegex(content, r"(?m)^NAME=.*CambonOS")

    def test_gtk_theme_has_a_single_declared_theme_identity(self):
        theme = PACKAGES / "cambonos-gtk-theme/files/themes/CambonOS-dark/index.theme"
        self.assertIn("CambonOS-dark", theme.read_text(encoding="utf-8"))

    def test_branding_identity_assets_are_well_formed(self):
        import xml.etree.ElementTree as ET
        package = PACKAGES / "cambonos-branding" / "files"
        for asset in ("cambonos-icon.svg", "cambonos-text.svg"):
            with self.subTest(asset=asset):
                ET.parse(package / asset)

    def test_lightdm_configuration_is_parseable_and_selects_a_greeter(self):
        package = PACKAGES / "cambonos-lightdm" / "files"
        parser = configparser.ConfigParser()
        parser.read(package / "lightdm/50-cambonos.conf", encoding="utf-8")
        self.assertIn("Seat:*", parser)
        self.assertTrue(parser["Seat:*"].get("greeter-session"))

    def test_plymouth_theme_declares_its_script_module(self):
        theme = PACKAGES / "cambonos-plymouth/files/themes/cambonos/cambonos.plymouth"
        parser = configparser.ConfigParser()
        parser.read(theme, encoding="utf-8")
        self.assertEqual(parser["Plymouth Theme"].get("ModuleName"), "script")
        self.assertTrue(parser["script"].get("ScriptFile"))

    def test_shell_prompt_configuration_is_valid_toml(self):
        config = PACKAGES / "cambonos-shell-prompt/files/starship.toml"
        parsed = tomllib.loads(config.read_text(encoding="utf-8"))
        self.assertIn("palettes", parsed)
        self.assertIn("cambonos", parsed["palettes"])

    def test_zsh_package_provides_its_core_shell_configuration(self):
        package = PACKAGES / "cambonos-zsh/files/zsh/conf.d"
        for fragment in ("10-completion.zsh", "20-keybindings.zsh", "30-history.zsh"):
            with self.subTest(fragment=fragment):
                self.assertTrue((package / fragment).is_file())


if __name__ == "__main__":
    unittest.main()
