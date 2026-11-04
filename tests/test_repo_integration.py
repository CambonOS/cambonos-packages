import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-repo"
HELPER = PACKAGE / "files" / "lib" / "manage-pacman-include"

START = "# >>> cambonos-repo: managed by cambonos-repo"
END = "# <<< cambonos-repo"
INCLUDE = "Include = /etc/pacman.d/cambonos.conf"


class RepoIntegrationTests(unittest.TestCase):
    def run_helper(self, action, config):
        return subprocess.run(
            [str(HELPER), action, str(config)],
            text=True,
            capture_output=True,
            check=False,
        )

    def make_config(self, directory, content):
        path = Path(directory) / "pacman.conf"
        path.write_text(content, encoding="utf-8")
        return path

    def test_ensure_adds_managed_include_at_end(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(directory, "[options]\nColor\n\n[core]\nInclude = mirrorlist\n")
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text(encoding="utf-8")
            self.assertIn(START, content)
            self.assertIn(INCLUDE, content)
            self.assertIn(END, content)
            self.assertLess(content.index("[core]"), content.index(START))

    def test_ensure_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(directory, "[options]\n")
            self.assertEqual(self.run_helper("--ensure", config).returncode, 0)
            first = config.read_bytes()
            self.assertEqual(self.run_helper("--ensure", config).returncode, 0)
            self.assertEqual(config.read_bytes(), first)
            self.assertEqual(config.read_text().count(START), 1)

    def test_ensure_repairs_missing_include_inside_managed_block(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(
                directory,
                f"[options]\n{START}\n# Gestionado por cambonos-repo: desinstala el paquete para deshabilitarlo.\n{END}\n",
            )
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_text().count(INCLUDE), 1)

    def test_unmanaged_include_is_preserved_without_adopting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            original = f"[options]\n{INCLUDE}\n"
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_text(), original)
            self.assertNotIn(START, config.read_text())

    def test_managed_duplicate_is_removed_when_manual_include_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            original = (
                f"[options]\n{INCLUDE}\n\n{START}\n{INCLUDE}\n{END}\n"
            )
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text()
            self.assertEqual(content.count(INCLUDE), 1)
            self.assertNotIn(START, content)

    def test_unmanaged_include_without_final_newline_is_byte_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            original = f"[options]\n{INCLUDE}"
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_text(), original)

    def test_remove_preserves_unmanaged_include(self):
        with tempfile.TemporaryDirectory() as directory:
            original = (
                f"[options]\n{INCLUDE}\n\n{START}\n{INCLUDE}\n{END}\n"
            )
            config = self.make_config(directory, original)
            result = self.run_helper("--remove", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text()
            self.assertEqual(content.count(INCLUDE), 1)
            self.assertNotIn(START, content)

    def test_remove_deletes_only_managed_block(self):
        with tempfile.TemporaryDirectory() as directory:
            original = (
                f"[options]\nColor\n\n{START}\n{INCLUDE}\n{END}\n\n"
                "[core]\nInclude = mirrorlist\n"
            )
            config = self.make_config(directory, original)
            result = self.run_helper("--remove", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text()
            self.assertNotIn(START, content)
            self.assertNotIn(END, content)
            self.assertIn("[options]\nColor", content)
            self.assertIn("[core]\nInclude = mirrorlist", content)

    def test_incomplete_markers_fail_without_modifying_file(self):
        with tempfile.TemporaryDirectory() as directory:
            original = f"[options]\n{START}\n{INCLUDE}\n"
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_text(), original)
            self.assertIn("marcadores incompletos", result.stderr)

    def test_missing_config_fails_without_creating_it(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "missing-pacman.conf"
            result = self.run_helper("--ensure", config)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(config.exists())

    def test_package_metadata_and_repository_policy(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        repo_conf = (PACKAGE / "files" / "cambonos.conf").read_text(encoding="utf-8")
        hook = (PACKAGE / "files" / "hooks" / "cambonos-repo-pacman-conf.hook").read_text(encoding="utf-8")
        self.assertIn("pkgname=cambonos-repo", pkgb)
        self.assertIn("'cambonos-keyring'", pkgb)
        self.assertIn("backup=('etc/pacman.d/cambonos.conf')", pkgb)
        self.assertIn("https://mirror.cambonos.org/stable/$arch", repo_conf)
        self.assertIn("https://mirror.cambonos.org/testing/$arch", repo_conf)
        self.assertIn("SigLevel = Required TrustedOnly", repo_conf)
        self.assertLess(repo_conf.index("#[cambonos-testing]"), repo_conf.index("[cambonos]"))
        self.assertIn("Type = Path", hook)
        self.assertIn("Target = etc/pacman.conf", hook)
        self.assertIn("When = PostTransaction", hook)


if __name__ == "__main__":
    unittest.main()
