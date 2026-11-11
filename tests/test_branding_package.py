import os
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-branding"
FILES = PACKAGE / "files"
PKGBUILD = PACKAGE / "PKGBUILD"

CANONICAL_SVGS = {"cambonos-icon.svg", "cambonos-text.svg"}
CANONICAL_PNGS = {"cambonos-icon.png", "cambonos-text.png"}
PLYMOUTH_ASSETS = {
    "plymouth-background.png",
    "progress-background.png.base64",
    "progress-foreground.png.base64",
}
CONSOLE_ASSETS = {"console-colors", "90-cambonos-console-colors.rules"}
XFCE_TERMINAL_ASSETS = {"hooks", "lib", "xfce-terminalrc"}
GRAPHIC_ASSETS = CANONICAL_SVGS | CANONICAL_PNGS | {"plymouth-background.png"}
REMOVED_ASSETS = {
    "cambonos-icon-black.svg",
    "cambonos-icon-white.svg",
    "cambonos-text-black.svg",
    "cambonos-text-white.svg",
    "cambonos-logo.txt",
}
PNG_DIMENSIONS = {
    "cambonos-icon.png": (1024, 1024),
    "cambonos-text.png": (3792, 1024),
    "plymouth-background.png": (3840, 2160),
}


class BrandingPackageTests(unittest.TestCase):
    def test_source_contains_graphic_assets_license_and_integration_assets(self):
        names = {path.name for path in FILES.iterdir()}
        self.assertEqual(
            names,
            GRAPHIC_ASSETS
            | PLYMOUTH_ASSETS
            | CONSOLE_ASSETS
            | XFCE_TERMINAL_ASSETS
            | {"LICENSE", "dialogrc"},
        )
        self.assertTrue((FILES / "lib/manage-xfce-terminal").is_file())
        self.assertTrue((FILES / "hooks/cambonos-branding-xfce-terminal.hook").is_file())
        self.assertTrue((FILES / "xfce-terminalrc").is_file())
        self.assertFalse(REMOVED_ASSETS.intersection(names))

    def test_pkgbuild_installs_svg_png_and_integration_assets(self):
        content = PKGBUILD.read_text(encoding="utf-8")
        for name in sorted(GRAPHIC_ASSETS):
            self.assertIn(f'"$branding_dir/{name}"', content)
        self.assertIn('"$startdir/files/progress-background.png.base64"', content)
        self.assertIn('"$startdir/files/progress-foreground.png.base64"', content)
        self.assertIn('"$branding_dir/progress-background.png"', content)
        self.assertIn('"$branding_dir/progress-foreground.png"', content)
        self.assertIn(
            "depends=('bash' 'coreutils' 'gawk' 'kbd')", content
        )
        self.assertIn("pkgver=0.1.2", content)
        self.assertNotIn("fontconfig", content)
        self.assertNotIn("CambonOS-Symbols", content)
        self.assertIn("pkgrel=3", content)
        self.assertIn("backup=('etc/dialogrc')", content)
        self.assertIn('"$startdir/files/dialogrc"', content)
        self.assertIn('"$pkgdir/etc/dialogrc"', content)
        self.assertIn("install=cambonos-branding.install", content)
        self.assertIn('"$branding_dir/console-colors"', content)
        self.assertIn(
            '"$udev_rules_dir/90-cambonos-console-colors.rules"', content
        )
        self.assertIn('"$pkgdir/usr/share/cambonos/branding/xfce-terminalrc"', content)
        self.assertIn('"$pkgdir/usr/lib/cambonos-branding/manage-xfce-terminal"', content)
        self.assertIn('"$libalpm_hooks_dir/cambonos-branding-xfce-terminal.hook"', content)
        self.assertIn('"$pkgdir/usr/share/licenses/$pkgname/LICENSE"', content)
        self.assertNotIn("/usr/share/icons/", content)
        self.assertNotIn("/usr/share/pixmaps/", content)
        for removed in REMOVED_ASSETS:
            self.assertNotIn(removed, content)

    def test_console_palette_uses_the_approved_ansi_order(self):
        expected = [
            "#061C31",
            "#A63E4B",
            "#149246",
            "#B3973D",
            "#019FA7",
            "#994B78",
            "#258A96",
            "#F7F5EC",
            "#254359",
            "#F2767F",
            "#AEFA50",
            "#F3D45B",
            "#70E7E6",
            "#E879AD",
            "#62D5DF",
            "#FFFFFF",
        ]
        palette = (
            (FILES / "console-colors")
            .read_text(encoding="utf-8")
            .strip()
            .splitlines()
        )
        self.assertEqual(palette, expected)

    def test_udev_rule_applies_palette_to_virtual_terminals(self):
        rule = (FILES / "90-cambonos-console-colors.rules").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            rule.strip(),
            'SUBSYSTEM=="tty", KERNEL=="tty[1-9]*", ACTION=="add", '
            'RUN+="/usr/bin/setvtrgb -C /dev/%k '
            "/usr/share/cambonos/branding/console-colors\"",
        )

    def test_xfce_terminal_hook_tracks_package_lifecycle(self):
        hook = (FILES / "hooks/cambonos-branding-xfce-terminal.hook").read_text(
            encoding="utf-8"
        )
        self.assertIn("Operation = Install", hook)
        self.assertIn("Operation = Upgrade", hook)
        self.assertIn("Operation = Remove", hook)
        self.assertIn("Type = Package", hook)
        self.assertIn("Target = xfce4-terminal", hook)
        self.assertIn("When = PostTransaction", hook)
        self.assertIn(
            "Exec = /usr/lib/cambonos-branding/manage-xfce-terminal --sync", hook
        )
        self.assertIn("post_install()", (PACKAGE / "cambonos-branding.install").read_text())
        self.assertIn("post_upgrade()", (PACKAGE / "cambonos-branding.install").read_text())
        self.assertIn("pre_remove()", (PACKAGE / "cambonos-branding.install").read_text())

    def test_canonical_svgs_are_well_formed_xml(self):
        for name in sorted(CANONICAL_SVGS):
            with self.subTest(asset=name):
                ET.parse(FILES / name)

    def test_canonical_pngs_have_expected_dimensions(self):
        for name, expected_dimensions in PNG_DIMENSIONS.items():
            with self.subTest(asset=name):
                content = (FILES / name).read_bytes()
                self.assertGreaterEqual(len(content), 24)
                self.assertEqual(content[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(content[12:16], b"IHDR")
                dimensions = (
                    int.from_bytes(content[16:20], "big"),
                    int.from_bytes(content[20:24], "big"),
                )
                self.assertEqual(dimensions, expected_dimensions)



class XfceTerminalDefaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cambonos-xfce-terminal-")
        self.root = Path(self.temp.name)
        self.config_dir = self.root / "etc/xdg/xfce4/terminal"
        self.config = self.config_dir / "terminalrc"
        self.state = self.root / "var/lib/cambonos-branding/xfce4-terminal"
        self.fake_bin = self.root / "bin"
        self.fake_bin.mkdir()
        self.installed_marker = self.root / "xfce4-terminal-installed"
        self.helper = self.root / "manage-xfce-terminal"

        source = (FILES / "lib/manage-xfce-terminal").read_text(encoding="utf-8")
        source = source.replace(
            '"/etc/xdg/xfce4/terminal"', f'"{self.config_dir}"'
        )
        source = source.replace(
            '"/etc/xdg/xfce4/terminal/terminalrc"', f'"{self.config}"'
        )
        source = source.replace(
            '"/var/lib/cambonos-branding/xfce4-terminal"', f'"{self.state}"'
        )
        source = source.replace(
            '"/usr/share/cambonos/branding/xfce-terminalrc"',
            f'"{FILES / "xfce-terminalrc"}"',
        )
        self.assertIn(f'CONFIG_DIR="{self.config_dir}"', source)
        self.assertIn('CONFIG_FILE="$CONFIG_DIR/terminalrc"', source)
        self.assertIn(f'STATE_DIR="{self.state}"', source)
        self.assertNotIn('CONFIG_DIR="/etc/xdg/', source)
        self.assertNotIn('STATE_DIR="/var/lib/', source)
        self.assertNotIn('"/etc/xdg/', source)
        self.helper.write_text(source, encoding="utf-8")
        pacman = self.fake_bin / "pacman"
        pacman.write_text(
            '#!/usr/bin/bash\n[[ -f "$TEST_XFCE_INSTALLED" ]]\n', encoding="utf-8"
        )
        pacman.chmod(0o755)

    def tearDown(self):
        self.temp.cleanup()

    def run_helper(self, *args):
        env = os.environ.copy()
        env["PATH"] = f"{self.fake_bin}:{env['PATH']}"
        env["TEST_XFCE_INSTALLED"] = str(self.installed_marker)
        return subprocess.run(
            ["bash", str(self.helper), *args],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_sync_and_remove_restore_existing_global_configuration(self):
        self.config_dir.mkdir(parents=True)
        original = (
            "[Configuration]\n"
            "FontName=Monospace 10\n"
            "ColorUseTheme=TRUE\n"
            "ColorBackground=#101010\n"
            "ColorForeground=#EEEEEE\n"
            "ColorPalette=old-palette\n"
            "MiscAlwaysShowTabs=TRUE\n"
        )
        self.config.write_text(original, encoding="utf-8")
        self.installed_marker.touch()

        result = self.run_helper("--sync")
        self.assertEqual(result.returncode, 0, result.stderr)
        configured = self.config.read_text(encoding="utf-8")
        self.assertIn("ColorUseTheme=FALSE", configured)
        self.assertIn("ColorBackground=#061C31", configured)
        self.assertIn("ColorForeground=#F7F5EC", configured)
        self.assertIn("ColorPalette=#061C31;#A63E4B;", configured)
        self.assertIn("FontName=Monospace 10", configured)
        self.assertIn("MiscAlwaysShowTabs=TRUE", configured)

        self.installed_marker.unlink()
        result = self.run_helper("--sync")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config.read_text(encoding="utf-8"), original)
        self.assertFalse(self.state.exists())

    def test_sync_does_nothing_when_terminal_is_not_installed(self):
        result = self.run_helper("--sync")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.state.exists())

    def test_remove_deletes_managed_config_when_no_original_existed(self):
        self.installed_marker.touch()
        result = self.run_helper("--sync")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.config.is_file())

        self.installed_marker.unlink()
        result = self.run_helper("--sync")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.state.exists())

    def test_remove_preserves_administrator_edits(self):
        self.config_dir.mkdir(parents=True)
        original = (
            "[Configuration]\n"
            "FontName=Monospace 10\n"
            "ColorUseTheme=TRUE\n"
            "ColorBackground=#101010\n"
            "ColorForeground=#EEEEEE\n"
            "ColorPalette=old-palette\n"
        )
        self.config.write_text(original, encoding="utf-8")
        self.installed_marker.touch()
        result = self.run_helper("--sync")
        self.assertEqual(result.returncode, 0, result.stderr)

        configured = self.config.read_text(encoding="utf-8")
        configured = configured.replace("ColorBackground=#061C31", "ColorBackground=#ABCDEF")
        configured += "MiscAlwaysShowTabs=TRUE\n"
        self.config.write_text(configured, encoding="utf-8")
        self.installed_marker.unlink()
        result = self.run_helper("--sync")
        self.assertEqual(result.returncode, 0, result.stderr)

        restored = self.config.read_text(encoding="utf-8")
        self.assertIn("ColorBackground=#ABCDEF", restored)
        self.assertIn("ColorUseTheme=TRUE", restored)
        self.assertIn("ColorForeground=#EEEEEE", restored)
        self.assertIn("ColorPalette=old-palette", restored)
        self.assertIn("MiscAlwaysShowTabs=TRUE", restored)
        self.assertFalse(self.state.exists())



if __name__ == "__main__":
    unittest.main()
