import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "cambonos-pacman"
HELPER = PACKAGE / "files" / "lib" / "manage-pacman-config"
OPTIONS_START = "# >>> cambonos-pacman: managed options"
OPTIONS_END = "# <<< cambonos-pacman: managed options"
REPOS_START = "# >>> cambonos-pacman: managed repositories"
REPOS_END = "# <<< cambonos-pacman: managed repositories"
LEGACY_START = "# >>> cambonos-repo: managed by cambonos-repo"
LEGACY_END = "# <<< cambonos-repo"
OPTIONS_INCLUDE = "Include = /etc/pacman.d/cambonos-options.conf"
REPOS_INCLUDE = "Include = /etc/pacman.d/cambonos.conf"


class PacmanIntegrationTests(unittest.TestCase):
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

    def test_ensure_adds_options_inside_options_and_repositories_at_end(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(directory, "[options]\nColor\n\n[core]\nInclude = mirrorlist\n")
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text(encoding="utf-8")
            self.assertIn(OPTIONS_START, content)
            self.assertIn(OPTIONS_INCLUDE, content)
            self.assertIn(OPTIONS_END, content)
            self.assertIn(REPOS_START, content)
            self.assertIn(REPOS_INCLUDE, content)
            self.assertIn(REPOS_END, content)
            self.assertLess(content.index("[options]"), content.index(OPTIONS_START))
            self.assertLess(content.index(OPTIONS_END), content.index("[core]"))
            self.assertLess(content.index("[core]"), content.index(REPOS_START))

    def test_ensure_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(directory, "[options]\n")
            self.assertEqual(self.run_helper("--ensure", config).returncode, 0)
            first = config.read_bytes()
            self.assertEqual(self.run_helper("--ensure", config).returncode, 0)
            self.assertEqual(config.read_bytes(), first)
            self.assertEqual(config.read_text().count(OPTIONS_START), 1)
            self.assertEqual(config.read_text().count(REPOS_START), 1)

    def test_ensure_collapses_duplicate_complete_managed_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            original = (
                "[options]\n"
                f"{OPTIONS_START}\n{OPTIONS_INCLUDE}\n{OPTIONS_END}\n"
                f"{OPTIONS_START}\n{OPTIONS_INCLUDE}\n{OPTIONS_END}\n"
                "[core]\n"
                f"{REPOS_START}\n{REPOS_INCLUDE}\n{REPOS_END}\n"
                f"{REPOS_START}\n{REPOS_INCLUDE}\n{REPOS_END}\n"
            )
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text()
            self.assertEqual(content.count(OPTIONS_START), 1)
            self.assertEqual(content.count(REPOS_START), 1)
            self.assertEqual(content.count(OPTIONS_INCLUDE), 1)
            self.assertEqual(content.count(REPOS_INCLUDE), 1)

    def test_duplicate_options_sections_fail_without_modifying_file(self):
        with tempfile.TemporaryDirectory() as directory:
            original = "[options]\nColor\n[core]\nInclude = mirrorlist\n[options]\n"
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_text(), original)

    def test_ensure_repairs_missing_managed_includes(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(
                directory,
                f"[options]\n{OPTIONS_START}\n{OPTIONS_END}\n\n"
                f"[core]\n{REPOS_START}\n{REPOS_END}\n",
            )
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text()
            self.assertEqual(content.count(OPTIONS_INCLUDE), 1)
            self.assertEqual(content.count(REPOS_INCLUDE), 1)

    def test_manual_options_include_is_preserved_without_managed_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            original = f"[options]\n{OPTIONS_INCLUDE}\n\n[core]\n"
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_text(), original + REPOS_START + "\n"
                             "# Gestionado por cambonos-pacman: desinstala el paquete para deshabilitar los repositorios.\n"
                             + REPOS_INCLUDE + "\n" + REPOS_END + "\n")
            self.assertNotIn(OPTIONS_START, config.read_text())

    def test_manual_repository_include_is_preserved_without_managed_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            original = f"[options]\n\n[core]\n{REPOS_INCLUDE}\n"
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text()
            self.assertEqual(content.count(REPOS_INCLUDE), 1)
            self.assertNotIn(REPOS_START, content)
            self.assertIn(OPTIONS_INCLUDE, content)

    def test_legacy_repository_block_is_migrated(self):
        with tempfile.TemporaryDirectory() as directory:
            original = (
                "[options]\nColor\n\n[core]\n"
                f"{LEGACY_START}\n"
                "# Gestionado por cambonos-repo: desinstala el paquete para deshabilitarlo.\n"
                "Include = /etc/pacman.d/cambonos.conf\n"
                f"{LEGACY_END}\n"
            )
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text()
            self.assertNotIn(LEGACY_START, content)
            self.assertNotIn(LEGACY_END, content)
            self.assertEqual(content.count(REPOS_INCLUDE), 1)
            self.assertIn(OPTIONS_INCLUDE, content)
            self.assertIn(REPOS_START, content)

    def test_remove_deletes_both_managed_blocks_and_preserves_surrounding_config(self):
        with tempfile.TemporaryDirectory() as directory:
            original = "[options]\nColor\n\n[core]\nInclude = mirrorlist\n"
            config = self.make_config(directory, original)
            self.assertEqual(self.run_helper("--ensure", config).returncode, 0)
            result = self.run_helper("--remove", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text()
            self.assertNotIn(OPTIONS_START, content)
            self.assertNotIn(REPOS_START, content)
            self.assertIn("[options]\nColor", content)
            self.assertIn("[core]\nInclude = mirrorlist", content)

    def test_remove_without_managed_blocks_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            original = b"[options]\nColor"
            config = Path(directory) / "pacman.conf"
            config.write_bytes(original)
            result = self.run_helper("--remove", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_bytes(), original)

    def test_ensure_with_both_manual_includes_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            original = f"[options]\n{OPTIONS_INCLUDE}\n[core]\n{REPOS_INCLUDE}".encode()
            config = Path(directory) / "pacman.conf"
            config.write_bytes(original)
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_bytes(), original)

    def test_remove_preserves_manual_includes(self):
        with tempfile.TemporaryDirectory() as directory:
            original = f"[options]\n{OPTIONS_INCLUDE}\n\n[core]\n{REPOS_INCLUDE}\n"
            config = self.make_config(directory, original)
            result = self.run_helper("--remove", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_text(), original)

    def test_incomplete_or_mismatched_markers_fail_without_modifying_file(self):
        samples = (
            f"[options]\n{OPTIONS_START}\n{OPTIONS_INCLUDE}\n",
            f"[options]\n{OPTIONS_END}\n",
            f"[options]\n{OPTIONS_START}\n{REPOS_END}\n",
        )
        for sample in samples:
            with self.subTest(sample=sample), tempfile.TemporaryDirectory() as directory:
                config = self.make_config(directory, sample)
                original = config.read_bytes()
                result = self.run_helper("--ensure", config)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(config.read_bytes(), original)

    def test_missing_options_section_fails_without_modifying_file(self):
        with tempfile.TemporaryDirectory() as directory:
            original = "[core]\nInclude = mirrorlist\n"
            config = self.make_config(directory, original)
            result = self.run_helper("--ensure", config)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_text(), original)

    def test_missing_config_fails_without_creating_it(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "missing-pacman.conf"
            result = self.run_helper("--ensure", config)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(config.exists())

    def test_symlink_config_is_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.conf"
            target.write_text("[options]\n")
            link = Path(directory) / "pacman.conf"
            link.symlink_to(target)
            result = self.run_helper("--ensure", link)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_text(), "[options]\n")

    def test_file_without_final_newline_is_processed(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(directory, "[options]")
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = config.read_text()
            self.assertIn(OPTIONS_INCLUDE, content)
            self.assertIn(REPOS_INCLUDE, content)

    def test_mode_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(directory, "[options]\n")
            config.chmod(0o640)
            result = self.run_helper("--ensure", config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(os.stat(config).st_mode & 0o777, 0o640)

    def test_package_metadata_and_differential_configuration(self):
        pkgb = (PACKAGE / "PKGBUILD").read_text(encoding="utf-8")
        repo_conf = (PACKAGE / "files" / "cambonos.conf").read_text(encoding="utf-8")
        options_conf = (PACKAGE / "files" / "cambonos-options.conf").read_text(encoding="utf-8")
        hook = (PACKAGE / "files" / "hooks" / "cambonos-pacman-conf.hook").read_text(encoding="utf-8")
        self.assertIn("pkgname=cambonos-pacman", pkgb)
        self.assertIn("provides=('cambonos-repo')", pkgb)
        self.assertIn("conflicts=('cambonos-repo')", pkgb)
        self.assertIn("replaces=('cambonos-repo')", pkgb)
        self.assertIn("depends=('bash' 'coreutils' 'diffutils' 'gawk' 'cambonos-keyring')", pkgb)
        self.assertIn("'cambonos-keyring'", pkgb)
        self.assertIn("backup=('etc/pacman.d/cambonos.conf' 'etc/pacman.d/cambonos-options.conf')", pkgb)
        self.assertIn("https://mirror.cambonos.org/stable/$arch", repo_conf)
        self.assertIn("https://mirror.cambonos.org/testing/$arch", repo_conf)
        self.assertIn("SigLevel = Required TrustedOnly", repo_conf)
        self.assertLess(repo_conf.index("#[cambonos-testing]"), repo_conf.index("[cambonos]"))
        self.assertEqual(
            options_conf.splitlines(),
            ["Color", "CheckSpace", "VerbosePkgLists", "ParallelDownloads = 3", "ILoveCandy"],
        )
        self.assertNotIn("[options]", options_conf)
        self.assertNotIn("HoldPkg", options_conf)
        self.assertNotIn("SigLevel", options_conf)
        self.assertIn("Type = Path", hook)
        self.assertIn("Target = etc/pacman.conf", hook)
        self.assertIn("When = PostTransaction", hook)


if __name__ == "__main__":
    unittest.main()
