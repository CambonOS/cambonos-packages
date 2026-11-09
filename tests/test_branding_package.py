import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-branding"
FILES = PACKAGE / "files"
TTF_DIR = FILES / "ttf"
PKGBUILD = PACKAGE / "PKGBUILD"

CANONICAL_SVGS = {"cambonos-icon.svg", "cambonos-text.svg"}
CANONICAL_PNGS = {"cambonos-icon.png", "cambonos-text.png"}
PLYMOUTH_ASSETS = {
    "plymouth-background.png",
    "progress-background.png.base64",
    "progress-foreground.png.base64",
}
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
    def test_source_contains_graphic_assets_license_and_ttf_directory(self):
        names = {path.name for path in FILES.iterdir()}
        self.assertEqual(names, GRAPHIC_ASSETS | PLYMOUTH_ASSETS | {"LICENSE", "ttf"})
        self.assertTrue((TTF_DIR / "CambonOS-Symbols.ttf").is_file())
        self.assertTrue((TTF_DIR / "65-cambonos-symbols.conf").is_file())
        self.assertFalse(REMOVED_ASSETS.intersection(names))

    def test_pkgbuild_installs_svg_png_and_font_assets(self):
        content = PKGBUILD.read_text(encoding="utf-8")
        for name in sorted(GRAPHIC_ASSETS):
            self.assertIn(f'"$branding_dir/{name}"', content)
        self.assertIn('"$startdir/files/progress-background.png.base64"', content)
        self.assertIn('"$startdir/files/progress-foreground.png.base64"', content)
        self.assertIn('"$branding_dir/progress-background.png"', content)
        self.assertIn('"$branding_dir/progress-foreground.png"', content)
        self.assertIn('"$font_dir/CambonOS-Symbols.ttf"', content)
        self.assertIn('"$fontconfig_avail/65-cambonos-symbols.conf"', content)
        self.assertIn('"$fontconfig_default/65-cambonos-symbols.conf"', content)
        self.assertIn('"$pkgdir/usr/share/licenses/$pkgname/LICENSE"', content)
        self.assertNotIn("/usr/share/icons/", content)
        self.assertNotIn("/usr/share/pixmaps/", content)
        for removed in REMOVED_ASSETS:
            self.assertNotIn(removed, content)

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

    def test_fontconfig_rule_is_well_formed_and_targets_private_use_codepoint(self):
        path = TTF_DIR / "65-cambonos-symbols.conf"
        ET.parse(path)
        content = path.read_text(encoding="utf-8")
        self.assertIn("<int>1114109</int>", content)
        self.assertIn("<string>CambonOS Symbols</string>", content)

    def test_ttf_has_a_valid_sfnt_signature(self):
        signature = (TTF_DIR / "CambonOS-Symbols.ttf").read_bytes()[:4]
        self.assertIn(signature, {b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"})



if __name__ == "__main__":
    unittest.main()
