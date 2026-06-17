from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SBOM_MODULE = "cad_agent.tools.generate_sbom"
PROVENANCE_MODULE = "cad_agent.tools.provenance"
RUNNER = ROOT / "run_cad_agent.sh"


class ScriptContractTest(unittest.TestCase):
    def _run_script(self, module: str, output: Path, *extra_args: str, env: dict[str, str] | None = None) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", module, "--output", str(output), *extra_args],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
            env={**os.environ, **(env or {})},
        )
        self.assertEqual(completed.returncode, 0)

    def _run_runner_command(self, output: Path, command: str) -> None:
        completed = subprocess.run(
            [str(RUNNER), command, "--output", str(output)],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0)

    def test_sbom_shape_and_deterministic_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "sbom-1.json"
            second = Path(temp_dir) / "sbom-2.json"
            self._run_script(SBOM_MODULE, first)
            self._run_script(SBOM_MODULE, second)

            first_text = first.read_text(encoding="utf-8")
            second_text = second.read_text(encoding="utf-8")
            self.assertEqual(first_text, second_text)

            sbom = json.loads(first_text)
            self.assertEqual(sbom["spdxVersion"], "SPDX-2.3")
            self.assertEqual(sbom["dataLicense"], "CC0-1.0")
            self.assertEqual(sbom["creationInfo"]["created"], "1970-01-01T00:00:00Z")
            self.assertIn("cad-agent-framework", sbom["project"]["name"])
            self.assertGreaterEqual(len(sbom["packages"]), 1)
            self.assertTrue(any(package["name"] == "cad-agent-framework" for package in sbom["packages"]))
            self.assertTrue(any(package["name"] == "cadquery" for package in sbom["packages"]))
            self.assertTrue(any(package["artifact_hashes"] for package in sbom["packages"]))
            self.assertTrue(any(any(hash_entry["type"] == "wheel" for hash_entry in package["artifact_hashes"]) for package in sbom["packages"]))

    def test_provenance_shape_and_deterministic_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "provenance-1.json"
            second = Path(temp_dir) / "provenance-2.json"
            self._run_script(PROVENANCE_MODULE, first)
            self._run_script(PROVENANCE_MODULE, second)

            first_text = first.read_text(encoding="utf-8")
            second_text = second.read_text(encoding="utf-8")
            self.assertEqual(first_text, second_text)

            provenance = json.loads(first_text)
            self.assertEqual(provenance["_type"], "https://in-toto.io/Statement/v1")
            self.assertEqual(provenance["predicateType"], "https://slsa.dev/provenance/v1")
            self.assertEqual(provenance["predicate"]["buildDefinition"]["buildType"], "local://cad-agent-framework/skeleton")
            self.assertEqual(provenance["predicate"]["runDetails"]["builder"]["id"], "local://cad-agent-framework/scripts/provenance.py")
            self.assertTrue(provenance["predicate"]["runDetails"]["metadata"]["stub"])
            self.assertEqual(provenance["subject"][0]["name"], "cad-agent-framework")
            self.assertEqual(len(provenance["subject"][0]["digest"]["sha256"]), 64)

    def test_source_date_epoch_controls_provenance_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "provenance.json"
            self._run_script(
                PROVENANCE_MODULE,
                output,
                env={"SOURCE_DATE_EPOCH": "1700000000"},
            )
            provenance = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(provenance["predicate"]["runDetails"]["metadata"]["startedOn"], "2023-11-14T22:13:20Z")

    def test_runner_exposes_sbom_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sbom = Path(temp_dir) / "sbom.json"
            provenance = Path(temp_dir) / "provenance.json"
            self._run_runner_command(sbom, "sbom")
            self._run_runner_command(provenance, "provenance")

            self.assertEqual(json.loads(sbom.read_text(encoding="utf-8"))["SPDXID"], "SPDXRef-DOCUMENT")
            self.assertEqual(json.loads(provenance.read_text(encoding="utf-8"))["predicateType"], "https://slsa.dev/provenance/v1")


if __name__ == "__main__":
    unittest.main()
