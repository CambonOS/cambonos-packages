"""Contracts for the isolated build and trusted publication workflows."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BUILD_WORKFLOW = ROOT / ".github/workflows/package-build.yml"
PUBLISH_WORKFLOW = ROOT / ".github/workflows/package-publish.yml"


def load_workflow(path: Path) -> tuple[str, dict]:
    source = path.read_text(encoding="utf-8")
    return source, yaml.load(source, Loader=yaml.BaseLoader)


class PipelineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_source, cls.build = load_workflow(BUILD_WORKFLOW)
        cls.publish_source, cls.publish = load_workflow(PUBLISH_WORKFLOW)

    def test_build_and_publish_are_separate_workflows(self):
        self.assertEqual(self.build["name"], "CambonOS package build")
        self.assertEqual(self.publish["name"], "CambonOS package publish")
        self.assertIn("push", self.build["on"])
        self.assertIn("workflow_run", self.publish["on"])
        self.assertFalse((ROOT / ".github/workflows/package-pipeline.yml").exists())

    def test_build_only_runs_for_supported_branches_and_has_no_secrets(self):
        branches = self.build["on"]["push"]["branches"]
        self.assertEqual(set(branches), {"dev", "main"})
        self.assertEqual(
            self.build["on"]["repository_dispatch"]["types"],
            ["external-package-updated"],
        )
        self.assertEqual(self.build["concurrency"]["group"], "cambonos-package-build")
        self.assertEqual(self.build["concurrency"]["cancel-in-progress"], "false")
        self.assertNotIn("CAMBONOS_SIGNING_KEY", self.build_source)
        self.assertNotIn("CAMBONOS_SIGNING_PASSPHRASE", self.build_source)
        self.assertNotIn("environment:", self.build_source)
        self.assertEqual(self.build["permissions"].get("contents"), "read")

    def test_build_runs_tests_and_arch_shell_validation(self):
        jobs = self.build["jobs"]
        self.assertIn("validate", jobs)
        self.assertIn("build", jobs)
        validate_steps = jobs["validate"]["steps"]
        self.assertTrue(any("unittest discover -s tests" in s.get("run", "")
                            for s in validate_steps))
        dispatch_step = next(s for s in validate_steps
                             if s.get("name") == "Validate external package dispatch")
        self.assertIn("validate_external_dispatch.py", dispatch_step["run"])
        self.assertIn("merge-base --is-ancestor", dispatch_step["run"])
        self.assertIn("DISPATCH_COMMIT", dispatch_step.get("env", {}))
        shell_step = next(s for s in validate_steps
                          if s.get("name") == "Validate Zsh and Fish syntax in Arch container")
        for required in (
            'docker run --rm --platform linux/amd64', '${ARCH_IMAGE}',
            'source-dev:/source-dev:ro', 'source-main:/source-main:ro',
            'pacman -Syu --noconfirm', 'pacman -S --needed --noconfirm zsh fish',
            'zsh -n', 'fish --no-execute',
        ):
            self.assertIn(required, shell_step["run"])

    def test_build_uploads_both_unsigned_channels_and_baseline(self):
        jobs = self.build["jobs"]
        self.assertIn("validate", jobs["build"].get("needs", []))
        uploads = [s for s in jobs["build"]["steps"]
                   if s.get("uses", "").startswith("actions/upload-artifact")]
        names = {s.get("with", {}).get("name") for s in uploads}
        self.assertEqual(names, {"build-${{ matrix.channel }}"})
        self.assertIn("previous-publication-manifest", self.build_source)
        self.assertIn("name: build-context", self.build_source)
        self.assertIn("schema_version: 2", self.build_source)
        self.assertIn('external_sources', self.build_source)
        self.assertIn('Attach external source snapshots to build manifest', self.build_source)
        self.assertIn("retention-days: 2", self.build_source)

    def test_publish_is_workflow_run_gated_and_serialized(self):
        trigger = self.publish["on"]["workflow_run"]
        self.assertEqual(trigger["workflows"], ["CambonOS package build"])
        self.assertEqual(trigger["types"], ["completed"])
        self.assertEqual(self.publish["concurrency"]["group"],
                         "cambonos-package-publication")
        self.assertEqual(self.publish["concurrency"]["cancel-in-progress"], "false")

    def test_publish_uses_trusted_main_code_and_exact_run_artifacts(self):
        self.assertIn("ref: refs/heads/main", self.publish_source)
        self.assertIn("github.event.workflow_run.id", self.publish_source)
        self.assertIn("name: build-context", self.publish_source)
        self.assertIn("steps.context.outputs.bootstrap == 'false'", self.publish_source)
        self.assertIn("actions/download-artifact@v8.0.2", self.publish_source)
        self.assertIn("run-id: ${{ github.event.workflow_run.id }}", self.publish_source)
        self.assertIn(".path | endswith(\".github/workflows/package-build.yml\")",
                      self.publish_source)
        self.assertIn('"repository_dispatch"', self.publish_source)
        self.assertIn("check_external_snapshot CambonOS/cambonos-installer", self.publish_source)
        self.assertIn("check_external_snapshot CambonOS/cambonos-mkiso", self.publish_source)
        self.assertIn(".external_sources[\"cambonos-installer\"]", self.publish_source)
        self.assertIn("git ls-remote --heads origin", self.publish_source)
        self.assertIn("EXPECTED_DEV_SHA", self.publish_source)
        self.assertIn("EXPECTED_MAIN_SHA", self.publish_source)
        self.assertIn("El mirror cambió desde el build", self.publish_source)

    def test_signing_secrets_are_confined_to_trusted_publish_workflow(self):
        self.assertNotIn("CAMBONOS_SIGNING_KEY", self.build_source)
        self.assertNotIn("CAMBONOS_SIGNING_PASSPHRASE", self.build_source)
        self.assertIn("secrets.CAMBONOS_SIGNING_KEY", self.publish_source)
        self.assertIn("secrets.CAMBONOS_SIGNING_PASSPHRASE", self.publish_source)
        self.assertIn("environment: package-signing", self.publish_source)

    def test_publish_fails_closed_and_deploy_depends_on_signing(self):
        jobs = self.publish["jobs"]
        self.assertIn("conclusion == 'success'", jobs["sign"]["if"])
        self.assertIn("Reject stale or mismatched build artifacts", self.publish_source)
        self.assertEqual(jobs["deploy"].get("needs"), "sign")
        self.assertEqual(jobs["deploy"]["environment"]["name"], "github-pages")

    def test_every_multiline_bash_entrypoint_uses_strict_mode(self):
        for workflow_name, workflow in (("build", self.build), ("publish", self.publish)):
            for job_name, job in workflow.get("jobs", {}).items():
                for step in job.get("steps", []):
                    if step.get("shell") == "bash" and "run" in step:
                        with self.subTest(workflow=workflow_name, job=job_name,
                                          step=step.get("name", "unnamed")):
                            self.assertIn("set -Eeuo pipefail", step["run"])

    def test_public_cli_exposes_pipeline_operations(self):
        cli = ROOT / "scripts/cambonos.py"
        for command in ("validate", "plan", "build", "recover-artifacts",
                        "compare-shadow", "sign"):
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, str(cli), command, "--help"],
                    cwd=ROOT, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
