import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util


def load_lint_module():
    path = Path(__file__).resolve().parent.parent / "tools" / "lint_packet.py"
    spec = importlib.util.spec_from_file_location("lint_packet", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class LintPacketTests(unittest.TestCase):
    def setUp(self):
        self.lint_module = load_lint_module()
        self.schema_path = Path(__file__).resolve().parent.parent / "pcp_lite.schema.json"

    def _write_manifest(self, directory: Path, manifest: dict) -> Path:
        manifest_path = directory / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path

    def test_valid_manifest_passes_lint(self):
        manifest = {
            "mission": "Test mission",
            "current_reality": ["fact one"],
            "constraints": ["constraint one"],
            "acceptance": ["acceptance one"],
            "required_artifacts": ["artifact one"],
            "failure_modes": ["failure one"],
            "substage_gate": ["gate one"],
        }

        with TemporaryDirectory() as tmp:
            manifest_path = self._write_manifest(Path(tmp), manifest)
            errors = self.lint_module.lint_file(manifest_path, self.schema_path)
            self.assertEqual(errors, [])

    def test_missing_required_section_reports_error(self):
        manifest = {
            "mission": "Test mission",
            "current_reality": ["fact one"],
            "constraints": ["constraint one"],
            "acceptance": [],
            "required_artifacts": ["artifact one"],
            "failure_modes": ["failure one"],
            "substage_gate": ["gate one"],
        }

        with TemporaryDirectory() as tmp:
            manifest_path = self._write_manifest(Path(tmp), manifest)
            errors = self.lint_module.lint_file(manifest_path, self.schema_path)
            self.assertTrue(any("acceptance" in err for err in errors))

    def test_cli_reports_success_and_failure(self):
        valid_manifest = {
            "mission": "CLI mission",
            "current_reality": ["fact one"],
            "constraints": ["constraint one"],
            "acceptance": ["acceptance one"],
            "required_artifacts": ["artifact one"],
            "failure_modes": ["failure one"],
            "substage_gate": ["gate one"],
        }

        invalid_manifest = {
            "mission": "",
            "current_reality": [],
            "constraints": ["constraint one"],
            "acceptance": ["acceptance one"],
            "required_artifacts": ["artifact one"],
            "failure_modes": ["failure one"],
            "substage_gate": ["gate one"],
        }

        script_path = Path(__file__).resolve().parent.parent / "tools" / "lint_packet.py"

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            valid_path = self._write_manifest(tmp_path, valid_manifest)
            result = subprocess.run(
                [sys.executable, str(script_path), str(valid_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("Lint passed", result.stdout)

            invalid_path = self._write_manifest(tmp_path, invalid_manifest)
            result = subprocess.run(
                [sys.executable, str(script_path), str(invalid_path)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("current reality", result.stdout)


if __name__ == "__main__":
    unittest.main()
