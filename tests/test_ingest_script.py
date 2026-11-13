from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "ingest.py"


class IngestScriptTests(unittest.TestCase):
    def test_script_generates_both_chunk_files_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "chunks"
            environment = {
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
            }
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
                check=False,
            )

            self.assertEqual(
                completed.returncode,
                0,
                msg=completed.stderr,
            )

            fixed_path = output_dir / "chunks_fixo.jsonl"
            markdown_path = output_dir / "chunks_markdown.jsonl"
            summary_path = output_dir / "summary.json"

            self.assertTrue(fixed_path.is_file())
            self.assertTrue(markdown_path.is_file())
            self.assertTrue(summary_path.is_file())

            for path in (fixed_path, markdown_path):
                lines = path.read_text(encoding="utf-8").splitlines()
                self.assertGreater(len(lines), 0)
                for line in lines:
                    payload = json.loads(line)
                    self.assertIn("chunk_id", payload)
                    self.assertIn("doc_id", payload)
                    self.assertIn("text", payload)
                    self.assertIn("metadata", payload)

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["document_count"], 3)
            strategies = {
                item["strategy"]: item for item in summary["strategies"]
            }
            self.assertEqual(set(strategies), {"fixo", "markdown"})
            self.assertEqual(strategies["fixo"]["chunk_size"], 800)
            self.assertEqual(strategies["fixo"]["chunk_overlap"], 150)
            self.assertEqual(strategies["markdown"]["chunk_size"], 800)
            self.assertEqual(strategies["markdown"]["chunk_overlap"], 100)


if __name__ == "__main__":
    unittest.main()
