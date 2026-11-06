import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-grub"
FILES = PACKAGE / "files"
THEME = FILES / "themes" / "CambonOS"


class GrubPackageTests(unittest.TestCase):
    def test_metadata_dependencies_and_backup_policy(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        self.assertIn("pkgname=cambonos-grub", pkgb)
        self.assertIn("pkgver=0.1.0", pkgb)
        self.assertIn("pkgrel=8", pkgb)
        self.assertIn("'GPL-3.0-only'", pkgb)
        self.assertIn("'GPL-2.0-or-later WITH Font-exception-2.0'", pkgb)
        self.assertIn("'grub>=2:2.16'", pkgb)
        self.assertIn("'os-prober'", pkgb)
        self.assertIn("backup=('etc/default/grub.d/60-cambonos.cfg')", pkgb)
        self.assertNotIn("/etc/default/grub\"", pkgb)

    def test_every_theme_asset_is_referenced_by_pkgbuild(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        referenced = set(re.findall(r'"\$startdir/files/(themes/CambonOS/[^\"]+)"', pkgb))
        actual = {
            str(path.relative_to(FILES))
            for path in THEME.rglob("*")
            if path.is_file()
        }
        self.assertEqual(referenced, actual)
        self.assertIn("themes/CambonOS/background.png", referenced)
        self.assertIn("themes/CambonOS/icons/cambonos.png", referenced)
        self.assertIn("themes/CambonOS/icons/windows.png", referenced)
        self.assertIn("themes/CambonOS/icons/linux.png", referenced)
        self.assertIn("themes/CambonOS/icons/oracle.png", referenced)
        self.assertIn("themes/CambonOS/icons/pop__os.png", referenced)
        self.assertIn("themes/CambonOS/icons/batocera_linux.png", referenced)

    def test_icon_names_match_os_prober_classes(self):
        icon_dir = THEME / "icons"
        names = {path.name for path in icon_dir.glob("*.png")}
        self.assertEqual(
            {name for name in names if "-" in name},
            {"linux-lite.png", "linux-mint.png"},
        )
        self.assertTrue(
            {
                "almalinux.png", "alpine.png", "amazon.png", "arch.png",
                "batocera_linux.png", "bodhi.png", "centos.png", "elementary.png",
                "garuda.png", "kali.png", "linux.png", "oracle.png", "pop__os.png",
                "puppy.png", "raspberry.png", "red.png", "rocky.png", "suse.png",
                "void.png", "zorin.png",
            }.issubset(names)
        )

    def test_grub_defaults_keep_ipv6_and_multiboot_enabled(self):
        config = (FILES / "defaults" / "60-cambonos.cfg").read_text(encoding="utf-8")
        self.assertIn('GRUB_DISTRIBUTOR="CambonOS"', config)
        self.assertIn('GRUB_CMDLINE_LINUX_DEFAULT="splash quiet loglevel=3"', config)
        self.assertIn("GRUB_GFXMODE=auto", config)
        self.assertIn("GRUB_DISABLE_OS_PROBER=false", config)
        self.assertIn("GRUB_DISABLE_SUBMENU=true", config)
        self.assertIn("GRUB_DISABLE_RECOVERY=false", config)
        self.assertNotIn("ipv6.disable=1", config)
        self.assertNotIn("GRUB_GFXPAYLOAD_LINUX", config)
        self.assertNotIn("1920x1080", config)

    def test_theme_uses_cambonos_palette_and_vimix_layout_assets(self):
        theme = (THEME / "theme.txt").read_text(encoding="utf-8")
        self.assertIn('desktop-image: "background.png"', theme)
        self.assertIn('desktop-image-scale-method: "padding"', theme)
        self.assertIn('terminal-box: "terminal_box_*.png"', theme)
        self.assertIn('selected_item_pixmap_style = "select_*.png"', theme)
        self.assertIn("icon_width = 32", theme)
        self.assertIn("icon_height = 32", theme)
        self.assertIn("item_icon_space = 12", theme)
        self.assertIn("item_height = 36", theme)
        self.assertIn("item_spacing = 12", theme)
        self.assertEqual(theme.count('desktop-color: "#061C31"'), 1)
        self.assertEqual(theme.count('item_color = "#F7F5EC"'), 1)
        self.assertEqual(theme.count('selected_item_color = "#70E7E6"'), 1)
        self.assertEqual(theme.count('color = "#AEFA50"'), 1)
        for color in ("#000000", "#cccccc", "#ffffff"):
            self.assertNotIn(color, theme)
        self.assertEqual(theme.count("+ boot_menu {"), 1)
        self.assertEqual(theme.count("+ label {"), 1)

    def test_hook_regenerates_after_kernel_install_upgrade_and_removal(self):
        hook = (FILES / "hooks" / "cambonos-grub-kernel.hook").read_text(
            encoding="utf-8"
        )
        for operation in ("Install", "Upgrade", "Remove"):
            self.assertIn(f"Operation = {operation}", hook)
        self.assertIn("Type = Path", hook)
        self.assertIn("Target = usr/lib/modules/*/vmlinuz", hook)
        self.assertIn("When = PostTransaction", hook)
        self.assertIn("Exec = /usr/lib/cambonos-grub/regenerate-grub-config", hook)

    def test_regenerator_guards_missing_and_non_regular_output(self):
        helper = FILES / "lib" / "regenerate-grub-config"
        content = helper.read_text(encoding="utf-8")
        self.assertIn("/boot/grub/grub.cfg", content)
        self.assertIn("! -e \"$grub_cfg\" && ! -L \"$grub_cfg\"", content)
        self.assertIn("! -f \"$grub_cfg\" || -L \"$grub_cfg\"", content)
        self.assertIn("exec /usr/bin/grub-mkconfig -o \"$grub_cfg\"", content)
        self.assertNotIn("grub-install", content)

    def test_scriptlets_regenerate_for_package_lifecycle(self):
        scriptlet = (PACKAGE / "cambonos-grub.install").read_text(encoding="utf-8")
        for function in ("post_install", "post_upgrade", "post_remove"):
            self.assertIn(f"{function}()", scriptlet)
        self.assertIn("/usr/bin/grub-mkconfig -o \"$grub_cfg\"", scriptlet)
        self.assertNotIn("grub-install", scriptlet)

    def test_license_and_upstream_notice_are_present(self):
        self.assertEqual((FILES / "LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())
        unifont_license = (FILES / "LICENSE-UNIFONT").read_text(encoding="utf-8")
        self.assertIn("GNU GENERAL PUBLIC LICENSE", unifont_license)
        exception = (FILES / "UNIFONT-FONT-EXCEPTION").read_text(encoding="utf-8")
        self.assertIn("embed this font", exception)
        notice = (FILES / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("Vinceliuice", notice)
        self.assertIn("GPL-3.0", notice)
        self.assertIn("Unifont", notice)
        self.assertIn("GPL-2.0-or-later", notice)
        self.assertIn("grub2-themes", notice)

    def test_package_scripts_have_valid_bash_syntax(self):
        paths = (
            PACKAGE / "PKGBUILD",
            PACKAGE / "cambonos-grub.install",
            FILES / "lib" / "regenerate-grub-config",
        )
        for path in paths:
            with self.subTest(path=path.name):
                result = subprocess.run(
                    ["bash", "-n", str(path)], text=True, capture_output=True, check=False
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_readme_documents_automation_and_limits(self):
        readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertIn("grub-mkconfig", readme)
        self.assertIn("os-prober", readme)
        self.assertIn("no ejecuta `grub-install`", readme)
        self.assertIn("IPv6 permanece habilitado", readme)
        self.assertIn("GRUB_GFXMODE", readme)


if __name__ == "__main__":
    unittest.main()