"""Repository-wide checks for syntax and common packaging hazards."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_syntax(command: list[str], path: Path) -> None:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(
            f"Error de sintaxis en {path.relative_to(ROOT)}:\n"
            f"{result.stdout}{result.stderr}"
        )


class TransversalSyntaxTests(unittest.TestCase):
    def test_all_python_sources_compile(self):
        sources = sorted(
            p for folder in ("scripts", "tests")
            for p in (ROOT / folder).rglob("*.py")
        )
        self.assertTrue(sources)
        for source in sources:
            with self.subTest(path=source.relative_to(ROOT)):
                compile(source.read_text(encoding="utf-8"), str(source), "exec")

    def test_all_pkgbuilds_and_install_scripts_are_valid_bash(self):
        candidates = sorted(ROOT.glob("packages/*/PKGBUILD"))
        candidates += sorted(ROOT.glob("packages/*/*.install"))
        self.assertTrue(candidates)
        for source in candidates:
            with self.subTest(path=source.relative_to(ROOT)):
                run_syntax(["bash", "-n", str(source)], source)

    def test_all_shell_scripts_are_syntactically_valid(self):
        candidates = []
        for package in (ROOT / "packages").iterdir():
            if not package.is_dir():
                continue
            for source in package.rglob("*"):
                if not source.is_file():
                    continue
                if source.suffix in {".sh", ".bash"} or source.name in {
                    "manage-pacman-config", "regenerate-grub-config",
                    "integrate-shells", "integrate-bash", "integrate-zsh",
                    "restore-release-files", "cambonos-fastfetch",
                    "cambonos-starship-directory",
                }:
                    candidates.append(source)
        candidates += [p for p in (ROOT / "scripts").rglob("*") if p.is_file() and p.suffix == ".sh"]
        for source in sorted(set(candidates)):
            with self.subTest(path=source.relative_to(ROOT)):
                run_syntax(["bash", "-n", str(source)], source)

    def test_zsh_fragments_when_zsh_is_available(self):
        interpreter = shutil.which("zsh")
        if not interpreter:
            self.skipTest("zsh no está instalado; CI debe instalarlo")
        sources = sorted((ROOT / "packages").rglob("*.zsh"))
        for source in sources:
            with self.subTest(path=source.relative_to(ROOT)):
                run_syntax([interpreter, "-n", str(source)], source)

    def test_fish_fragments_when_fish_is_available(self):
        interpreter = shutil.which("fish")
        if not interpreter:
            self.skipTest("fish no está instalado; CI debe instalarlo")
        sources = sorted((ROOT / "packages").rglob("*.fish"))
        for source in sources:
            with self.subTest(path=source.relative_to(ROOT)):
                run_syntax([interpreter, "--no-execute", str(source)], source)

    def test_json_resources_are_valid(self):
        resources = sorted((ROOT / "packages").rglob("*.json"))
        for source in resources:
            with self.subTest(path=source.relative_to(ROOT)):
                json.loads(source.read_text(encoding="utf-8"))

    def test_package_symlinks_do_not_escape_the_repository(self):
        for source in (ROOT / "packages").rglob("*"):
            if source.is_symlink():
                with self.subTest(path=source.relative_to(ROOT)):
                    resolved = source.resolve()
                    self.assertTrue(
                        resolved == ROOT or ROOT in resolved.parents,
                        f"Enlace simbólico fuera del repositorio: {source}",
                    )


if __name__ == "__main__":
    unittest.main()
