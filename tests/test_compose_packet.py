import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util


def load_compose_module():
    path = Path(__file__).resolve().parent.parent / "tools" / "compose_packet.py"
    spec = importlib.util.spec_from_file_location("compose_packet", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ComposePacketTests(unittest.TestCase):
    def setUp(self):
        self.compose_module = load_compose_module()

    def test_compose_generates_expected_artifacts(self):
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
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "input.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            original_cwd = Path.cwd()
            os.chdir(tmp_path)
            try:
                self.compose_module.compose(str(manifest_path))
            finally:
                os.chdir(original_cwd)

            normalized_expected = self.compose_module.normalize_manifest(manifest)
            context_sha_expected = (
                self.compose_module.compute_context_sha(normalized_expected) + "\n"
            )

            self.assertEqual(
                (tmp_path / "manifest.json").read_text(encoding="utf-8"),
                normalized_expected,
            )
            self.assertEqual(
                (tmp_path / "context_sha").read_text(encoding="utf-8"),
                context_sha_expected,
            )

            packet_text = (tmp_path / "packet.md").read_text(encoding="utf-8")
            self.assertIn("# Context Packet Template (PCP-lite)", packet_text)
            self.assertIn("- Test mission", packet_text)
            self.assertIn("- fact one", packet_text)


if __name__ == "__main__":
    unittest.main()
