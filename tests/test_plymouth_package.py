import re
import struct
import subprocess
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-plymouth"
FILES = PACKAGE / "files"
THEME = FILES / "themes" / "cambonos"


class PlymouthPackageTests(unittest.TestCase):
    def test_metadata_dependencies_and_mkinitcpio_backup(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        self.assertIn("pkgname=cambonos-plymouth", pkgb)
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
            ("background.png", "3840 x 2160"),
            ("header-image.png", "512 x 512"),
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
        script = (THEME / "cambonos.script").read_text(encoding="utf-8")
        boot = theme.split("[boot-up]", 1)[1].split("[shutdown]", 1)[0]
        self.assertIn("ModuleName=script", theme)
        self.assertIn("ScriptFile=/usr/share/plymouth/themes/cambonos/cambonos.script", theme)
        self.assertIn("UseAnimation=false", boot)
        self.assertIn("UseProgressBar=true", boot)
        self.assertNotIn("UseAnimation=true", theme)
        self.assertIn("Plymouth.SetBootProgressFunction(boot_progress_callback)", script)
        self.assertIn("Plymouth.SetSystemUpdateFunction(system_update_callback)", script)

    def test_theme_centers_logo_and_places_progress_bar_below(self):
        script = (THEME / "cambonos.script").read_text(encoding="utf-8")
        self.assertIn("logo_vertical_alignment = 0.66", script)
        self.assertIn("progress_vertical_alignment = 0.7", script)
        self.assertIn("(window_width - logo_width) / 2", script)
        self.assertIn("(window_height - logo_height) * logo_vertical_alignment", script)
        self.assertIn("(window_height - progress_height) * progress_vertical_alignment", script)

    def test_logo_and_progress_scale_from_reference_resolution(self):
        script = (THEME / "cambonos.script").read_text(encoding="utf-8")
        self.assertIn("reference_width = 1920", script)
        self.assertIn("reference_height = 1080", script)
        self.assertIn("logo_original.Scale(logo_width, logo_height)", script)
        self.assertIn("progress_background_original.Scale(progress_width, progress_height)", script)
        self.assertIn("progress_foreground_original.Scale(filled_width, progress_height)", script)

    def test_background_and_palette_use_cambonos_brand(self):
        theme = (THEME / "cambonos.plymouth").read_text(encoding="utf-8")
        script = (THEME / "cambonos.script").read_text(encoding="utf-8")
        for value in (
            "ImageDir=/usr/share/plymouth/themes/cambonos",
            "ConsoleLogBackgroundColor=0x061C31",
        ):
            self.assertIn(value, theme)
        self.assertIn('Image("background.png")', script)
        self.assertIn('Image("progress-background.png")', script)
        self.assertIn('Image("progress-foreground.png")', script)
        for filename, color in (
            ("progress-background.png.base64", bytes.fromhex("29465A")),
            ("progress-foreground.png.base64", bytes.fromhex("70E7E6")),
        ):
            decoded = subprocess.run(
                ["base64", "--decode", str(THEME / filename)],
                capture_output=True,
                check=False,
            )
            self.assertEqual(decoded.returncode, 0, decoded.stderr.decode())
            self.assertTrue(decoded.stdout.startswith(b"\x89PNG\r\n\x1a\n"))
            offset = 8
            image_data = bytearray()
            while offset < len(decoded.stdout):
                chunk_size = struct.unpack_from(">I", decoded.stdout, offset)[0]
                chunk_type = decoded.stdout[offset + 4 : offset + 8]
                chunk_data = decoded.stdout[offset + 8 : offset + 8 + chunk_size]
                if chunk_type == b"IDAT":
                    image_data.extend(chunk_data)
                offset += chunk_size + 12
            self.assertEqual(zlib.decompress(image_data), b"\x00" + color + b"\xff")

    def test_theme_uses_immediate_transition_without_show_delay(self):
        theme = (THEME / "cambonos.plymouth").read_text(encoding="utf-8")
        self.assertIn("UseProgressBar=true", theme)
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



if __name__ == "__main__":
    unittest.main()