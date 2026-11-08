import configparser
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-lightdm"
FILES = PACKAGE / "files"


class LightDMPackageTests(unittest.TestCase):
    def test_pkgbuild_metadata_dependencies_backup_and_install_script(self):
        content = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        self.assertIn("pkgname=cambonos-lightdm", content)
        self.assertIn("pkgver=0.1.0", content)
        self.assertIn("pkgrel=3", content)
        self.assertIn("license=('GPL-3.0-only')", content)
        self.assertIn(
            "depends=('lightdm' 'lightdm-slick-greeter' 'numlockx' 'cambonos-gtk-theme')", content
        )
        self.assertIn(
            "backup=('etc/lightdm/lightdm.conf.d/50-cambonos.conf' 'etc/lightdm/slick-greeter.conf')",
            content,
        )
        self.assertIn("install=cambonos-lightdm.install", content)
        self.assertNotIn("papirus-icon-theme", content)
        self.assertNotIn("matcha-gtk-theme", content)
        self.assertNotIn("accountsservice", content)

    def test_lightdm_dropin_contains_only_shared_greeter_policy(self):
        path = FILES / "lightdm" / "50-cambonos.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(path, encoding="utf-8")
        self.assertEqual(parser.get("Seat:*", "greeter-session"), "lightdm-slick-greeter")
        self.assertEqual(parser.getboolean("Seat:*", "greeter-hide-users"), False)
        self.assertEqual(parser.getboolean("Seat:*", "greeter-show-manual-login"), False)
        self.assertEqual(parser.getboolean("Seat:*", "greeter-allow-guest"), False)
        self.assertEqual(parser.getboolean("Seat:*", "allow-guest"), False)
        self.assertFalse(parser.has_option("Seat:*", "user-session"))
        self.assertFalse(parser.has_option("Seat:*", "xserver-command"))

    def test_slick_greeter_config_selects_cambonos_gtk_theme(self):
        path = FILES / "slick-greeter" / "slick-greeter.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(path, encoding="utf-8")
        self.assertEqual(
            parser.get("Greeter", "background"),
            "/usr/share/cambonos/lightdm/background.png",
        )
        self.assertEqual(parser.getboolean("Greeter", "draw-user-backgrounds"), False)
        self.assertEqual(parser.getboolean("Greeter", "activate-numlock"), True)
        self.assertEqual(parser.get("Greeter", "enable-hidpi"), "auto")
        self.assertEqual(parser.get("Greeter", "theme-name"), "CambonOS-Dark")
        self.assertFalse(parser.has_option("Greeter", "icon-theme-name"))

    def test_graphic_assets_have_expected_signatures_and_dimensions(self):
        background = (FILES / "branding" / "background.png").read_bytes()
        self.assertEqual(background[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(
            (int.from_bytes(background[16:20], "big"), int.from_bytes(background[20:24], "big")),
            (3840, 2160),
        )
        self.assertEqual(background[25], 2, "background.png must use RGB color")

    def test_scriptlet_only_enables_when_no_display_manager_is_selected(self):
        path = PACKAGE / "cambonos-lightdm.install"
        content = path.read_text(encoding="utf-8")
        self.assertIn("post_install()", content)
        self.assertNotIn("post_upgrade()", content)
        self.assertNotIn("post_remove()", content)
        self.assertIn('[[ -e "$display_manager_link" || -L "$display_manager_link" ]]', content)
        self.assertIn('/usr/bin/systemctl --root="$root" enable lightdm.service', content)
        self.assertIn("_cambonos_lightdm_enable_service /", content)
        self.assertNotIn("enable --now", content)
        self.assertNotIn("disable lightdm.service", content)
        self.assertNotIn("--force", content)

    @unittest.skipUnless(shutil.which("systemctl"), "systemctl is not installed")
    def test_scriptlet_enables_only_when_no_display_manager_is_selected(self):
        scriptlet = PACKAGE / "cambonos-lightdm.install"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            unit_dir = root / "usr/lib/systemd/system"
            link_dir = root / "etc/systemd/system"
            unit_dir.mkdir(parents=True)
            link_dir.mkdir(parents=True)
            (unit_dir / "lightdm.service").write_text(
                "[Unit]\nDescription=Test LightDM\n"
                "[Service]\nExecStart=/usr/bin/true\n"
                "[Install]\nAlias=display-manager.service\n",
                encoding="utf-8",
            )

            enabled = subprocess.run(
                [
                    "bash", "-c",
                    'source "$1"; _cambonos_lightdm_enable_service "$2"',
                    "test", str(scriptlet), str(root),
                ],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(enabled.returncode, 0, enabled.stderr)
            display_manager = link_dir / "display-manager.service"
            self.assertTrue(display_manager.is_symlink())
            self.assertEqual(
                display_manager.readlink().as_posix(),
                "/usr/lib/systemd/system/lightdm.service",
            )

            # A pre-existing non-LightDM display manager must remain untouched.
            display_manager.unlink()
            display_manager.symlink_to("/usr/lib/systemd/system/sddm.service")
            preserved = subprocess.run(
                [
                    "bash", "-c",
                    'source "$1"; _cambonos_lightdm_enable_service "$2"',
                    "test", str(scriptlet), str(root),
                ],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(preserved.returncode, 0, preserved.stderr)
            self.assertEqual(
                display_manager.readlink().as_posix(),
                "/usr/lib/systemd/system/sddm.service",
            )
            self.assertIn("preserving existing display-manager.service", preserved.stderr)

    def test_scriptlet_has_valid_bash_syntax(self):
        for path in (PACKAGE / "PKGBUILD", PACKAGE / "cambonos-lightdm.install"):
            with self.subTest(path=path.name):
                result = subprocess.run(
                    ["bash", "-n", str(path)], text=True, capture_output=True, check=False
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_license_is_present_and_pkgbuild_installs_it(self):
        license_path = FILES / "LICENSE"
        self.assertTrue(license_path.is_file())
        self.assertIn("GNU GENERAL PUBLIC LICENSE", license_path.read_text(encoding="utf-8"))
        content = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        self.assertIn('"$startdir/files/LICENSE"', content)
        self.assertIn('"$pkgdir/usr/share/licenses/$pkgname/LICENSE"', content)


if __name__ == "__main__":
    unittest.main()
