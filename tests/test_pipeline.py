from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from obsidian_notebooklm_pipeline.recipes import expected_artifact_name, load_recipes
from obsidian_notebooklm_pipeline.stages.pack import run_pack
from obsidian_notebooklm_pipeline.stages.sync import run_sync

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
CORPUS_DIR = FIXTURES_DIR / "corpus"
READING_MAP_PATH = FIXTURES_DIR / "reading_map.json"
RECIPES_PATH = FIXTURES_DIR / "recipes.json"
MANUAL_SOURCE_UPDATES_PATH = FIXTURES_DIR / "manual_source_updates.json"


class PipelineStageTests(unittest.TestCase):
    def test_pack_uses_reading_map_order_and_stable_segment_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir) / "work"
            first_pack = run_pack(CORPUS_DIR, work_dir, READING_MAP_PATH)
            second_pack = run_pack(CORPUS_DIR, work_dir, READING_MAP_PATH)

        self.assertEqual(first_pack.selection_mode, "reading_map")
        self.assertEqual(
            [segment.source_path for segment in first_pack.segments],
            [
                "notes/applications.md",
                "notes/foundations.md",
                "reference/glossary.md",
            ],
        )
        self.assertEqual(
            [segment.segment_id for segment in first_pack.segments],
            [segment.segment_id for segment in second_pack.segments],
        )
        self.assertEqual(first_pack.segments[0].tags, ("core", "week-2"))
        self.assertNotIn("reference/ignored.md", [segment.source_path for segment in first_pack.segments])

    def test_sync_preserves_existing_synced_entries_on_partial_updates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir) / "work"
            run_pack(CORPUS_DIR, work_dir, READING_MAP_PATH)

            first_updates_path = Path(temp_dir) / "updates-step-1.json"
            first_updates_path.write_text(
                json.dumps(
                    {
                        "updates": [
                            {
                                "segment_id": "notes--applications",
                                "notebooklm_source_id": "source-applications",
                            }
                        ]
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            run_sync(work_dir, first_updates_path)

            second_updates_path = Path(temp_dir) / "updates-step-2.json"
            second_updates_path.write_text(
                json.dumps(
                    {
                        "updates": [
                            {
                                "segment_id": "notes--foundations",
                                "notebooklm_source_id": "source-foundations",
                            }
                        ]
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            source_map = run_sync(work_dir, second_updates_path)

            entries = {entry.segment_id: entry for entry in source_map.entries}
            handoff = json.loads((work_dir / "sync_handoff.json").read_text(encoding="utf-8"))

        self.assertEqual(entries["notes--applications"].notebooklm_source_id, "source-applications")
        self.assertEqual(entries["notes--applications"].sync_status, "synced")
        self.assertEqual(entries["notes--foundations"].notebooklm_source_id, "source-foundations")
        self.assertEqual(entries["reference--glossary"].sync_status, "pending")
        self.assertTrue(entries["notes--applications"].text_digest)
        self.assertEqual(len(handoff["pending_segments"]), 1)
        self.assertEqual(len(handoff["synced_segments"]), 2)

    def test_recipes_load_from_documented_file_format(self) -> None:
        recipes = load_recipes(RECIPES_PATH)

        self.assertEqual([recipe.artifact_kind for recipe in recipes], ["slides", "audio", "report"])
        self.assertEqual(expected_artifact_name(recipes[0]), "fixture-slides.pdf")
        self.assertEqual(expected_artifact_name(recipes[1]), "fixture-audio.mp3")
        self.assertEqual(expected_artifact_name(recipes[2]), "fixture-report.md")

    def test_stage_smoke_flow_without_notebooklm_access(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir) / "work"
            downloads_dir = work_dir / "downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)

            self._run_cli(
                "pack",
                "--corpus-dir",
                str(CORPUS_DIR),
                "--work-dir",
                str(work_dir),
                "--reading-map",
                str(READING_MAP_PATH),
            )
            self._run_cli(
                "sync",
                "--work-dir",
                str(work_dir),
                "--source-ids",
                str(MANUAL_SOURCE_UPDATES_PATH),
            )
            self._run_cli(
                "generate",
                "--work-dir",
                str(work_dir),
                "--recipes",
                str(RECIPES_PATH),
            )

            for recipe in load_recipes(RECIPES_PATH):
                (downloads_dir / expected_artifact_name(recipe)).write_text(
                    f"downloaded artifact for {recipe.name}\n",
                    encoding="utf-8",
                )

            self._run_cli(
                "publish",
                "--work-dir",
                str(work_dir),
                "--downloads-dir",
                str(downloads_dir),
            )

            self.assertTrue((work_dir / "source_pack.json").exists())
            self.assertTrue((work_dir / "source_map.json").exists())
            self.assertTrue((work_dir / "sync_handoff.json").exists())
            self.assertTrue((work_dir / "generation_request.json").exists())
            self.assertTrue((work_dir / "publish_manifest.json").exists())
            self.assertTrue((work_dir / "outputs" / "slides" / "fixture-slides.pdf").exists())
            self.assertTrue((work_dir / "outputs" / "audio" / "fixture-audio.mp3").exists())
            self.assertTrue((work_dir / "outputs" / "report" / "fixture-report.md").exists())

            source_pack = json.loads((work_dir / "source_pack.json").read_text(encoding="utf-8"))
            source_map = json.loads((work_dir / "source_map.json").read_text(encoding="utf-8"))
            generation_request = json.loads((work_dir / "generation_request.json").read_text(encoding="utf-8"))
            publish_manifest = json.loads((work_dir / "publish_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(source_pack["selection_mode"], "reading_map")
        self.assertEqual(len(source_pack["segments"]), 3)
        self.assertEqual(len(source_map["entries"]), 3)
        self.assertEqual(generation_request["recipes_path"], str(RECIPES_PATH))
        self.assertEqual(generation_request["unsynced_segment_ids"], [])
        self.assertEqual([item["status"] for item in publish_manifest], ["published", "published", "published"])

    def _run_cli(self, *args: str) -> dict | list:
        result = subprocess.run(
            [sys.executable, "scripts/run_pipeline.py", *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()
