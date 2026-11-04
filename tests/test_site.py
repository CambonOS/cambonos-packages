from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.site import generate_directory_indexes, write_index


class DirectoryIndexTests(unittest.TestCase):
    def test_generates_nested_indexes_and_preserves_manual_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text("<h1>Branded landing page</h1>", encoding="utf-8")
            repository = site / "stable" / "x86_64"
            repository.mkdir(parents=True)
            (repository / "cambonos-1.0-1-any.pkg.tar.zst").write_bytes(b"package")
            (repository / "file with spaces.txt").write_text("content", encoding="utf-8")

            generated, skipped = generate_directory_indexes(site)

            self.assertEqual((generated, skipped), (2, 1))
            self.assertEqual(
                (site / "index.html").read_text(encoding="utf-8"),
                "<h1>Branded landing page</h1>",
            )
            channel_index = site / "stable" / "index.html"
            architecture_index = repository / "index.html"
            self.assertTrue(channel_index.is_file())
            self.assertTrue(architecture_index.is_file())
            html = architecture_index.read_text(encoding="utf-8")
            self.assertIn('href="file%20with%20spaces.txt"', html)
            self.assertIn("cambonos-1.0-1-any.pkg.tar.zst", html)
            self.assertIn("generated-by: cambonos-index", html)

    def test_updates_generated_indexes_but_keeps_manual_nested_indexes(self):
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "metadata").mkdir()
            (site / "metadata" / "index.html").write_text(
                "<h1>Manual metadata page</h1>", encoding="utf-8"
            )
            generated_dir = site / "stable"
            generated_dir.mkdir()
            generated_index = generated_dir / "index.html"
            generated_index.write_text(
                "<!-- generated-by: cambonos-index --><p>old</p>", encoding="utf-8"
            )
            (generated_dir / "new.db").write_bytes(b"db")

            generated, skipped = generate_directory_indexes(site)

            self.assertEqual((generated, skipped), (2, 1))
            self.assertIn("new.db", generated_index.read_text(encoding="utf-8"))
            self.assertEqual(
                (site / "metadata" / "index.html").read_text(encoding="utf-8"),
                "<h1>Manual metadata page</h1>",
            )

    def test_landing_page_orders_testing_before_enabled_stable(self):
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary)
            manifest = {
                "channels": {
                    "stable": {"branch": "main", "commit": "a" * 40, "packages": {}},
                    "testing": {"branch": "dev", "commit": "b" * 40, "packages": {}},
                }
            }
            write_index(site, manifest, "https://example.github.io/repo")
            html = (site / "index.html").read_text(encoding="utf-8")
            testing = html.index("#[cambonos-testing]")
            stable = html.index("[cambonos]", testing)
            self.assertLess(testing, stable)
            self.assertIn('href="stable/"', html)
            self.assertIn('href="testing/"', html)

    def test_empty_directory_gets_empty_listing(self):
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary)
            empty = site / "empty"
            empty.mkdir()
            generate_directory_indexes(site)
            self.assertIn("This directory is empty.", (empty / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
