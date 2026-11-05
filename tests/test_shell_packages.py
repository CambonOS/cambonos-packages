from __future__ import annotations

import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ShellPackageMetadataTests(unittest.TestCase):
    def test_zsh_package_has_required_runtime_dependencies(self):
        text = (ROOT / "packages/cambonos-zsh/PKGBUILD").read_text()
        for dependency in (
            "zsh", "zsh-completions", "zsh-autosuggestions",
            "zsh-syntax-highlighting", "cambonos-shell-prompt", "util-linux",
        ):
            self.assertIn(f"'{dependency}'", text)
        self.assertNotIn("cambonos-fastfetch", text)
        self.assertFalse((ROOT / "packages/cambonos-zsh/files/etc/skel/.zshrc").exists())

    def test_shell_prompt_is_independent_of_zsh_and_fish(self):
        text = (ROOT / "packages/cambonos-shell-prompt/PKGBUILD").read_text()
        self.assertIn("'starship'", text)
        self.assertIn("'bash'", text)
        self.assertIn("'util-linux'", text)
        self.assertNotIn("'zsh'", text)
        self.assertNotIn("'fish'", text.split("optdepends=", 1)[0])
        self.assertIn("vendor_conf.d/cambonos-shell-prompt.fish", text)
        self.assertIn("conf.d/50-shell-prompt.zsh", text)

    def test_fastfetch_uses_zsh_conf_d_and_shared_lock(self):
        package = (ROOT / "packages/cambonos-fastfetch/PKGBUILD").read_text()
        helper = (ROOT / "packages/cambonos-fastfetch/files/cambonos/lib/integrate-shells").read_text()
        self.assertIn("conf.d/60-fastfetch.zsh", package)
        self.assertIn("cambonos-shell-integration.lock", helper)
        self.assertNotIn("update_file \"$action\" \"$ZSH_RC\"", helper)
        self.assertIn("remove_legacy_zsh_block", helper)

    def test_starship_toml_parses_and_keeps_cambonos_identity(self):
        path = ROOT / "packages/cambonos-shell-prompt/files/starship.toml"
        config = tomllib.loads(path.read_text())
        self.assertEqual(config["palette"], "cambonos")
        self.assertEqual(config["palettes"]["cambonos"]["primary"], "#AEFA50")
        self.assertEqual(config["palettes"]["cambonos"]["accent"], "#70E7E6")
        self.assertIn("$git_branch", config["format"])
        self.assertIn("$status", config["right_format"])
        self.assertFalse(config["python"]["detect_files"])

    def test_all_managers_use_the_same_bash_lock(self):
        expected = "/run/lock/cambonos-shell-integration.lock"
        for path in (
            ROOT / "packages/cambonos-zsh/files/cambonos/lib/integrate-zsh",
            ROOT / "packages/cambonos-shell-prompt/files/cambonos/lib/integrate-bash",
            ROOT / "packages/cambonos-fastfetch/files/cambonos/lib/integrate-shells",
        ):
            self.assertIn(expected, path.read_text())


class ShellIntegrationHelperTests(unittest.TestCase):
    def _run_helper(self, source: Path, replacements: dict[str, str], action: str):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            helper = root / "helper"
            text = source.read_text()
            for old, new in replacements.items():
                text = text.replace(old, new)
            helper.write_text(text)
            helper.chmod(0o755)
            result = subprocess.run(
                ["bash", str(helper), action], text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            return root, result

    def test_prompt_bash_install_repair_remove_preserves_external_content(self):
        source = ROOT / "packages/cambonos-shell-prompt/files/cambonos/lib/integrate-bash"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bashrc = root / "etc/bash.bashrc"
            bashrc.parent.mkdir(parents=True)
            bashrc.write_text("# administrator configuration\n")
            fragment = root / "usr/share/cambonos/shell-prompt/shell/bash"
            fragment.parent.mkdir(parents=True)
            fragment.write_text("# prompt fragment\n")
            lock = root / "run/lock/cambonos-shell-integration.lock"
            lock.parent.mkdir(parents=True)
            helper = root / "helper"
            text = source.read_text().replace("/etc/bash.bashrc", str(bashrc))
            text = text.replace("/usr/share/cambonos/shell-prompt/shell/bash", str(fragment))
            text = text.replace("/run/lock/cambonos-shell-integration.lock", str(lock))
            text = text.replace("/usr/bin/bash", shutil.which("bash") or "/bin/bash")
            helper.write_text(text)
            helper.chmod(0o755)

            for action in ("install", "repair", "repair"):
                result = subprocess.run(["bash", str(helper), action], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            installed = bashrc.read_text()
            self.assertEqual(installed.count("# >>> CambonOS Shell Prompt >>>"), 1)
            self.assertIn("# administrator configuration", installed)

            result = subprocess.run(["bash", str(helper), "remove"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(bashrc.read_text(), "# administrator configuration\n")

    def test_prompt_helper_refuses_incomplete_markers_without_rewriting_bashrc(self):
        source = ROOT / "packages/cambonos-shell-prompt/files/cambonos/lib/integrate-bash"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bashrc = root / "etc/bash.bashrc"
            bashrc.parent.mkdir(parents=True)
            original = "# administrator config\n# >>> CambonOS Shell Prompt >>>\n"
            bashrc.write_text(original)
            fragment = root / "usr/share/cambonos/shell-prompt/shell/bash"
            fragment.parent.mkdir(parents=True)
            fragment.write_text("# fragment\n")
            lock = root / "run/lock/cambonos-shell-integration.lock"
            lock.parent.mkdir(parents=True)
            helper = root / "helper"
            text = source.read_text().replace("/etc/bash.bashrc", str(bashrc))
            text = text.replace("/usr/share/cambonos/shell-prompt/shell/bash", str(fragment))
            text = text.replace("/run/lock/cambonos-shell-integration.lock", str(lock))
            text = text.replace("/usr/bin/bash", shutil.which("bash") or "/bin/bash")
            helper.write_text(text)
            helper.chmod(0o755)
            result = subprocess.run(["bash", str(helper), "repair"], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(bashrc.read_text(), original)

    def test_zsh_manager_creates_and_removes_only_its_own_entry_file(self):
        source = ROOT / "packages/cambonos-zsh/files/cambonos/lib/integrate-zsh"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            etc_zsh = root / "etc/zsh"
            etc_zsh.mkdir(parents=True)
            state = root / "var/lib/cambonos-zsh"
            lock = root / "run/lock/cambonos-shell-integration.lock"
            lock.parent.mkdir(parents=True)
            helper = root / "helper"
            text = source.read_text()
            text = text.replace("/etc/zsh/zshrc", str(etc_zsh / "zshrc"))
            text = text.replace("/run/lock/cambonos-shell-integration.lock", str(lock))
            text = text.replace("/var/lib/cambonos-zsh", str(state))
            helper.write_text(text)
            helper.chmod(0o755)

            for action in ("install", "repair"):
                result = subprocess.run(["bash", str(helper), action], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            zshrc = etc_zsh / "zshrc"
            self.assertEqual(zshrc.read_text().count("# >>> CambonOS Zsh configuration >>>"), 1)
            result = subprocess.run(["bash", str(helper), "remove"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(zshrc.exists())

    def test_zsh_manager_preserves_preexisting_global_configuration(self):
        source = ROOT / "packages/cambonos-zsh/files/cambonos/lib/integrate-zsh"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            etc_zsh = root / "etc/zsh"
            etc_zsh.mkdir(parents=True)
            zshrc = etc_zsh / "zshrc"
            zshrc.write_text("# administrator Zsh configuration\n")
            state = root / "var/lib/cambonos-zsh"
            lock = root / "run/lock/cambonos-shell-integration.lock"
            lock.parent.mkdir(parents=True)
            helper = root / "helper"
            text = source.read_text()
            text = text.replace("/etc/zsh/zshrc", str(zshrc))
            text = text.replace("/run/lock/cambonos-shell-integration.lock", str(lock))
            text = text.replace("/var/lib/cambonos-zsh", str(state))
            helper.write_text(text)
            helper.chmod(0o755)
            for action in ("install", "remove"):
                result = subprocess.run(["bash", str(helper), action], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(zshrc.read_text(), "# administrator Zsh configuration\n")

    def test_fastfetch_upgrade_migrates_legacy_zsh_block_and_preserves_loader(self):
        source = ROOT / "packages/cambonos-fastfetch/files/cambonos/lib/integrate-shells"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            etc = root / "etc"
            (etc / "profile.d").mkdir(parents=True)
            (root / "usr/share/cambonos/fastfetch/shell").mkdir(parents=True)
            bashrc = etc / "bash.bashrc"
            bashrc.write_text("# bash administrator config\n")
            zshrc = etc / "zsh/zshrc"
            zshrc.parent.mkdir(parents=True)
            zshrc.write_text(
                "# local zsh config\n"
                "# >>> CambonOS Zsh configuration >>>\n"
                "# loader\n"
                "# <<< CambonOS Zsh configuration <<<\n"
                "# >>> CambonOS Fastfetch >>>\n"
                "# old Fastfetch integration\n"
                "# <<< CambonOS Fastfetch <<<\n"
            )
            fragment = root / "usr/share/cambonos/fastfetch/shell/bash"
            fragment.write_text("# fastfetch fragment\n")
            profile = etc / "profile.d/cambonos-fastfetch.sh"
            profile.write_text("# profile fragment\n")
            lock = root / "run/lock/cambonos-shell-integration.lock"
            lock.parent.mkdir(parents=True)
            helper = root / "helper"
            replacements = {
                "/etc/bash.bashrc": str(bashrc),
                "/usr/share/cambonos/fastfetch/shell/bash": str(fragment),
                "/etc/zsh/zshrc": str(zshrc),
                "/usr/share/cambonos/zsh/conf.d/60-fastfetch.zsh": str(root / "zsh-fragment"),
                "/etc/profile.d/cambonos-fastfetch.sh": str(profile),
                "/usr/share/fish/vendor_conf.d/cambonos-fastfetch.fish": str(root / "fish-fragment"),
                "/run/lock/cambonos-shell-integration.lock": str(lock),
                "/usr/bin/bash": shutil.which("bash") or "/bin/bash",
                "/usr/bin/fish": str(root / "fish-bin"),
                "/usr/bin/zsh": str(root / "zsh-bin"),
            }
            text = source.read_text()
            for old, new in replacements.items():
                text = text.replace(old, new)
            helper.write_text(text)
            helper.chmod(0o755)
            result = subprocess.run(["bash", str(helper), "repair"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            migrated = zshrc.read_text()
            self.assertIn("# local zsh config", migrated)
            self.assertIn("# >>> CambonOS Zsh configuration >>>", migrated)
            self.assertNotIn("# >>> CambonOS Fastfetch >>>", migrated)


if __name__ == "__main__":
    unittest.main()
