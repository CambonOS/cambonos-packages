"""Public workflow contracts: catch broken CI wiring without freezing its layout."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/package-pipeline.yml"


class PipelineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        # BaseLoader avoids YAML 1.1 coercing the GitHub key `on` to boolean.
        cls.workflow = yaml.load(cls.source, Loader=yaml.BaseLoader)

    def test_workflow_is_parseable_and_has_required_jobs(self):
        self.assertIsInstance(self.workflow, dict)
        jobs = self.workflow.get("jobs", {})
        for job in ("validate", "build", "signing", "publish"):
            self.assertIn(job, jobs, f"Falta el job esencial {job}")

    def test_workflow_runs_the_repository_test_suite(self):
        self.assertIn("unittest discover -s tests", self.source)

    def test_build_and_publication_jobs_depend_on_validation(self):
        jobs = self.workflow["jobs"]
        self.assertIn("validate", jobs["build"].get("needs", ""))
        needs = jobs["signing"].get("needs", [])
        self.assertIn("validate", needs)
        self.assertIn("build", needs)
        self.assertIn("signing", jobs["publish"].get("needs", ""))

    def test_workflow_uses_fail_fast_shell_execution(self):
        # Every multiline shell entrypoint must opt into strict Bash handling.
        steps = []
        for job in self.workflow["jobs"].values():
            steps.extend(job.get("steps", []))
        run_steps = [step for step in steps if "run" in step]
        self.assertTrue(run_steps)
        for step in run_steps:
            with self.subTest(step=step.get("name", "<unnamed>")):
                script = step["run"]
                if "shell" in step and step["shell"] == "bash":
                    self.assertIn("set -Eeuo pipefail", script)

    def test_workflow_has_read_only_default_permissions(self):
        self.assertEqual(self.workflow.get("permissions", {}).get("contents"), "read")

    def test_public_cli_exposes_the_pipeline_operations(self):
        cli = ROOT / "scripts/cambonos.py"
        for command in ("validate", "build", "sign"):
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, str(cli), command, "--help"],
                    cwd=ROOT, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
