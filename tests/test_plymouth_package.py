import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-plymouth"
FILES = PACKAGE / "files"
THEME = FILES / "themes" / "cambonos"


class PlymouthPackageTests(unittest.TestCase):
    def test_metadata_dependencies_and_mkinitcpio_backup(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        self.assertIn("pkgname=cambonos-plymouth", pkgb)
        self.assertIn("pkgver=0.1.0", pkgb)
        self.assertIn("pkgrel=2", pkgb)
        self.assertIn("depends=('plymouth' 'mkinitcpio>=36')", pkgb)
        self.assertIn(
            "backup=('etc/mkinitcpio.conf.d/90-cambonos-plymouth.conf')", pkgb
        )
        self.assertIn('"$pkgdir/usr/share/plymouth/themes/cambonos/"', pkgb)

    def test_all_theme_assets_are_packaged_without_spinner_frames(self):
        assets = {path.name for path in THEME.iterdir() if path.is_file()}
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        referenced = set(
            re.findall(r'"\$startdir/files/themes/cambonos/([^"]+)"', pkgb)
        )
        self.assertEqual(referenced, assets)
        self.assertIn("cambonos.plymouth", assets)
        self.assertIn("header-image.png", assets)
        self.assertIn("background.png", assets)
        self.assertFalse(any(name.startswith(("animation-", "throbber-")) for name in assets))
        for filename, dimensions in (
            ("background.png", "1920 x 1080"),
            ("header-image.png", "256 x 256"),
        ):
            result = subprocess.run(
                ["file", str(THEME / filename)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(dimensions, result.stdout)

    def test_theme_uses_progress_bar_without_spinner(self):
        theme = (THEME / "cambonos.plymouth").read_text(encoding="utf-8")
        boot = theme.split("[boot-up]", 1)[1].split("[shutdown]", 1)[0]
        self.assertIn("ScaleBackgroundImage=true", theme)
        self.assertIn("UseAnimation=false", boot)
        self.assertIn("UseProgressBar=true", boot)
        self.assertNotIn("UseAnimation=true", theme)

    def test_background_and_palette_use_cambonos_brand(self):
        theme = (THEME / "cambonos.plymouth").read_text(encoding="utf-8")
        for value in (
            "ImageDir=/usr/share/plymouth/themes/cambonos",
            "BackgroundStartColor=0x061C31",
            "BackgroundEndColor=0x061C31",
            "ProgressBarForegroundColor=0x70E7E6",
        ):
            self.assertIn(value, theme)

    def test_theme_uses_immediate_transition_without_show_delay(self):
        theme = (THEME / "cambonos.plymouth").read_text(encoding="utf-8")
        for value in (
            "Transition=none",
            "TransitionDuration=0.0",
            "UseProgressBar=true",
        ):
            self.assertIn(value, theme)
        self.assertNotIn("ShowDelay=", theme)

    def test_mkinitcpio_dropin_preserves_hooks_and_places_plymouth_safely(self):
        dropin = FILES / "mkinitcpio" / "90-cambonos-plymouth.conf"
        content = dropin.read_text(encoding="utf-8")
        for hooks, expected in (
            (
                "base udev autodetect block encrypt filesystems",
                "base udev autodetect block plymouth encrypt filesystems",
            ),
            (
                "base systemd autodetect block sd-encrypt filesystems",
                "base systemd autodetect block plymouth sd-encrypt filesystems",
            ),
            (
                "base udev autodetect block filesystems",
                "base udev plymouth autodetect block filesystems",
            ),
        ):
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    'HOOKS=( $1 ); source "$2"; printf "%s\\n" "${HOOKS[*]}"',
                    "test",
                    hooks,
                    str(dropin),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), expected)

        repeated = subprocess.run(
            [
                "bash",
                "-c",
                'HOOKS=( base udev plymouth filesystems ); source "$1"; printf "%s\\n" "${HOOKS[*]}"',
                "test",
                str(dropin),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertEqual(repeated.stdout.strip(), "base udev plymouth filesystems")
        self.assertRegex(
            content,
            re.compile(r"HOOKS=\(\"\$\{_cambonos_plymouth_hooks\[@\]\}\"\)"),
        )

    def test_lifecycle_selects_respects_and_resets_theme(self):
        scriptlet = (PACKAGE / "cambonos-plymouth.install").read_text(encoding="utf-8")
        self.assertIn("post_install()", scriptlet)
        self.assertIn("post_upgrade()", scriptlet)
        self.assertIn("post_remove()", scriptlet)
        self.assertIn("plymouth-set-default-theme cambonos", scriptlet)
        self.assertIn("plymouth-set-default-theme --reset", scriptlet)
        self.assertIn("mkinitcpio -P", scriptlet)

    def test_scripts_have_valid_bash_syntax(self):
        for path in (
            PACKAGE / "PKGBUILD",
            PACKAGE / "cambonos-plymouth.install",
            FILES / "mkinitcpio" / "90-cambonos-plymouth.conf",
        ):
            with self.subTest(path=path.name):
                result = subprocess.run(
                    ["bash", "-n", str(path)], text=True, capture_output=True, check=False
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_readme_documents_boot_arguments_and_configuration_limits(self):
        readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertIn("splash quiet", readme)
        self.assertIn("ShowDelay=0", readme)
        self.assertIn("/etc/mkinitcpio.conf.d/90-cambonos-plymouth.conf", readme)
        self.assertIn("ALL_config", readme)


if __name__ == "__main__":
    unittest.main()