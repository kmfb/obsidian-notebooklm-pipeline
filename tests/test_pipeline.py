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
from obsidian_notebooklm_pipeline.stages.generate import run_generate
from obsidian_notebooklm_pipeline.stages.pack import run_pack
from obsidian_notebooklm_pipeline.stages.publish import run_publish
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
        self.assertEqual(recipes[0].format, "presenter_slides")
        self.assertEqual(recipes[1].source_ids, ("source-applications", "source-glossary"))
        self.assertEqual(recipes[2].prompt, "Write an operator-facing roadmap report with milestones, risks, and next actions.")
        self.assertEqual(expected_artifact_name(recipes[0]), "fixture-slides.pdf")
        self.assertEqual(expected_artifact_name(recipes[1]), "fixture-audio.mp3")
        self.assertEqual(expected_artifact_name(recipes[2]), "fixture-report.md")

    def test_generate_assembles_effective_requests_and_nlm_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir) / "work"
            run_pack(CORPUS_DIR, work_dir, READING_MAP_PATH)
            run_sync(work_dir, MANUAL_SOURCE_UPDATES_PATH)

            stage_result = run_generate(
                work_dir,
                RECIPES_PATH,
                notebook_id="notebook-123",
                profile="team-profile",
            )
            generation_request = stage_result.request
            request_payload = json.loads((work_dir / "generation_request.json").read_text(encoding="utf-8"))

        self.assertEqual(generation_request.notebook_id, "notebook-123")
        self.assertEqual(generation_request.profile, "team-profile")
        self.assertEqual(generation_request.source_drift_status, "clean")
        self.assertEqual(generation_request.synced_source_ids, [
            "source-applications",
            "source-foundations",
            "source-glossary",
        ])
        self.assertEqual(generation_request.unsynced_segment_ids, [])

        recipe_requests = {
            request.recipe.name: request
            for request in generation_request.recipe_requests
        }
        slides_request = recipe_requests["fixture-slides"]
        self.assertEqual(slides_request.guard_status, "ready")
        self.assertEqual(slides_request.source_ids, generation_request.synced_source_ids)
        self.assertIn("--format", slides_request.command)
        self.assertIn("presenter_slides", slides_request.command)
        self.assertIn("--length", slides_request.command)
        self.assertIn("short", slides_request.command)
        self.assertIn("--focus", slides_request.command)
        self.assertIn("Teach the core sequence", slides_request.command)
        self.assertEqual(slides_request.command[:4], ["nlm", "slides", "create", "notebook-123"])
        self.assertEqual(slides_request.command[-2:], ["--profile", "team-profile"])

        audio_request = recipe_requests["fixture-audio"]
        self.assertEqual(audio_request.source_ids, ["source-applications", "source-glossary"])
        self.assertEqual(audio_request.source_segment_ids, ["notes--applications", "reference--glossary"])
        self.assertIn("--source-ids", audio_request.command)
        self.assertIn("source-applications,source-glossary", audio_request.command)

        report_request = recipe_requests["fixture-report"]
        self.assertEqual(report_request.source_paths, ["notes/foundations.md"])
        self.assertIn("--prompt", report_request.command)
        self.assertIn("Create Your Own", report_request.command)
        self.assertEqual(request_payload["recipe_requests"][0]["recipe"]["name"], "fixture-slides")
        self.assertEqual(request_payload["source_drift_status"], "clean")

    def test_generate_blocks_when_source_pack_has_drift_from_source_map(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            corpus_dir = Path(temp_dir) / "corpus"
            shutil.copytree(CORPUS_DIR, corpus_dir)

            work_dir = Path(temp_dir) / "work"
            run_pack(corpus_dir, work_dir, READING_MAP_PATH)
            run_sync(work_dir, MANUAL_SOURCE_UPDATES_PATH)

            foundations_path = corpus_dir / "notes" / "foundations.md"
            foundations_path.write_text(
                foundations_path.read_text(encoding="utf-8") + "\nFresh local drift line.\n",
                encoding="utf-8",
            )
            run_pack(corpus_dir, work_dir, READING_MAP_PATH)

            generation_request = run_generate(
                work_dir,
                RECIPES_PATH,
                notebook_id="notebook-123",
            ).request
            drift_payload = json.loads((work_dir / "source_drift.json").read_text(encoding="utf-8"))

        self.assertEqual(generation_request.source_drift_status, "drifted")
        self.assertEqual(generation_request.drifted_segment_ids, ["notes--foundations"])
        self.assertEqual(drift_payload["status"], "drifted")
        self.assertEqual(drift_payload["drifted_segment_ids"], ["notes--foundations"])
        self.assertIn("text_digest changed", drift_payload["changed_segments"][0]["reasons"])
        self.assertTrue(all(request.guard_status == "blocked" for request in generation_request.recipe_requests))
        self.assertTrue(
            all("re-run sync" in request.blocked_reasons[0] for request in generation_request.recipe_requests)
        )

    def test_generate_blocks_unpinned_recipe_when_source_map_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir) / "work"
            run_pack(CORPUS_DIR, work_dir, READING_MAP_PATH)

            partial_updates_path = Path(temp_dir) / "partial-updates.json"
            partial_updates_path.write_text(
                json.dumps(
                    {
                        "updates": [
                            {
                                "segment_id": "notes--applications",
                                "notebooklm_source_id": "source-applications",
                            },
                            {
                                "segment_id": "reference--glossary",
                                "notebooklm_source_id": "source-glossary",
                            },
                        ]
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            run_sync(work_dir, partial_updates_path)

            generation_request = run_generate(
                work_dir,
                RECIPES_PATH,
                notebook_id="notebook-123",
            ).request
            recipe_requests = {request.recipe.name: request for request in generation_request.recipe_requests}

        self.assertEqual(generation_request.unsynced_segment_ids, ["notes--foundations"])
        self.assertEqual(recipe_requests["fixture-slides"].guard_status, "blocked")
        self.assertIn("pending segments", recipe_requests["fixture-slides"].blocked_reasons[0])
        self.assertEqual(recipe_requests["fixture-audio"].guard_status, "ready")
        self.assertEqual(recipe_requests["fixture-report"].guard_status, "blocked")
        self.assertIn("source-foundations", recipe_requests["fixture-report"].blocked_reasons[0])

    def test_guarded_generation_executes_ready_requests_with_fake_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir) / "work"
            run_pack(CORPUS_DIR, work_dir, READING_MAP_PATH)
            run_sync(work_dir, MANUAL_SOURCE_UPDATES_PATH)

            commands: list[list[str]] = []

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                commands.append(command)
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=f"created {command[1]}",
                    stderr="",
                )

            stage_result = run_generate(
                work_dir,
                RECIPES_PATH,
                notebook_id="notebook-123",
                execute=True,
                runner=fake_runner,
            )
            generation_run = stage_result.run
            run_payload = json.loads((work_dir / "generation_run.json").read_text(encoding="utf-8"))

        self.assertIsNotNone(generation_run)
        assert generation_run is not None
        self.assertEqual(len(commands), 3)
        self.assertEqual([result.status for result in generation_run.results], ["created", "created", "created"])
        self.assertEqual(run_payload["results"][0]["stdout"], "created slides")

    def test_publish_recursively_finds_single_download_and_updates_run_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir) / "work"
            downloads_dir = work_dir / "downloads" / "batch-001"
            recipes_path = Path(temp_dir) / "recipes.json"
            recipes_path.write_text(
                json.dumps(
                    {
                        "recipes": [
                            {
                                "name": "nested-report",
                                "artifact_kind": "report",
                                "format": "Briefing Doc",
                                "source_ids": ["source-foundations"],
                            }
                        ]
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            run_pack(CORPUS_DIR, work_dir, READING_MAP_PATH)
            run_sync(work_dir, MANUAL_SOURCE_UPDATES_PATH)
            run_generate(work_dir, recipes_path)

            downloads_dir.mkdir(parents=True, exist_ok=True)
            nested_download = downloads_dir / "nested-report.md"
            nested_download.write_text("nested download\n", encoding="utf-8")

            publish_manifest = run_publish(work_dir, work_dir / "downloads")
            manifest_payload = json.loads((work_dir / "publish_manifest.json").read_text(encoding="utf-8"))
            run_metadata = json.loads((work_dir / "run_metadata.json").read_text(encoding="utf-8"))

        self.assertEqual(publish_manifest.artifacts[0].status, "published")
        self.assertEqual(publish_manifest.artifacts[0].source_path, str(nested_download))
        self.assertEqual(manifest_payload["downloads_dir"], str(work_dir / "downloads"))
        self.assertEqual(manifest_payload["artifacts"][0]["intake_candidates"], [str(nested_download)])
        self.assertEqual(run_metadata["publish_manifest"]["artifacts_by_status"]["published"], ["nested-report"])

    def test_publish_marks_ambiguous_downloads_without_copying(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir) / "work"
            downloads_dir = work_dir / "downloads"
            recipes_path = Path(temp_dir) / "recipes.json"
            recipes_path.write_text(
                json.dumps(
                    {
                        "recipes": [
                            {
                                "name": "ambiguous-report",
                                "artifact_kind": "report",
                                "format": "Briefing Doc",
                                "source_ids": ["source-foundations"],
                            }
                        ]
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            run_pack(CORPUS_DIR, work_dir, READING_MAP_PATH)
            run_sync(work_dir, MANUAL_SOURCE_UPDATES_PATH)
            run_generate(work_dir, recipes_path)

            (downloads_dir / "a").mkdir(parents=True, exist_ok=True)
            (downloads_dir / "b").mkdir(parents=True, exist_ok=True)
            (downloads_dir / "a" / "ambiguous-report.md").write_text("first\n", encoding="utf-8")
            (downloads_dir / "b" / "ambiguous-report.md").write_text("second\n", encoding="utf-8")

            publish_manifest = run_publish(work_dir, downloads_dir)

        self.assertEqual(publish_manifest.artifacts[0].status, "ambiguous")
        self.assertIsNone(publish_manifest.artifacts[0].output_path)
        self.assertEqual(len(publish_manifest.artifacts[0].intake_candidates), 2)

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
            generate_payload = self._run_cli(
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

            publish_payload = self._run_cli(
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
            self.assertFalse((work_dir / "generation_run.json").exists())
            self.assertTrue((work_dir / "publish_manifest.json").exists())
            self.assertTrue((work_dir / "source_drift.json").exists())
            self.assertTrue((work_dir / "run_metadata.json").exists())
            self.assertTrue((work_dir / "outputs" / "slides" / "fixture-slides.pdf").exists())
            self.assertTrue((work_dir / "outputs" / "audio" / "fixture-audio.mp3").exists())
            self.assertTrue((work_dir / "outputs" / "report" / "fixture-report.md").exists())

            source_pack = json.loads((work_dir / "source_pack.json").read_text(encoding="utf-8"))
            source_map = json.loads((work_dir / "source_map.json").read_text(encoding="utf-8"))
            source_drift = json.loads((work_dir / "source_drift.json").read_text(encoding="utf-8"))
            generation_request = json.loads((work_dir / "generation_request.json").read_text(encoding="utf-8"))
            publish_manifest = json.loads((work_dir / "publish_manifest.json").read_text(encoding="utf-8"))
            run_metadata = json.loads((work_dir / "run_metadata.json").read_text(encoding="utf-8"))

        self.assertEqual(source_pack["selection_mode"], "reading_map")
        self.assertEqual(len(source_pack["segments"]), 3)
        self.assertEqual(len(source_map["entries"]), 3)
        self.assertEqual(source_drift["status"], "clean")
        self.assertEqual(generate_payload["request"]["recipes_path"], str(RECIPES_PATH))
        self.assertIsNone(generate_payload["run"])
        self.assertEqual(generate_payload["request"]["notebook_id"], None)
        self.assertEqual(generate_payload["request"]["source_drift_status"], "clean")
        self.assertEqual(generation_request["unsynced_segment_ids"], [])
        self.assertTrue(all(item["guard_status"] == "blocked" for item in generation_request["recipe_requests"]))
        self.assertEqual([item["status"] for item in publish_manifest["artifacts"]], ["published", "published", "published"])
        self.assertEqual([item["status"] for item in publish_payload["artifacts"]], ["published", "published", "published"])
        self.assertEqual(run_metadata["source_drift"]["status"], "clean")
        self.assertEqual(run_metadata["publish_manifest"]["artifacts_by_status"]["published"], [
            "fixture-slides",
            "fixture-audio",
            "fixture-report",
        ])

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
