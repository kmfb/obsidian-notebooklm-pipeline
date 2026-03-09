#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from obsidian_notebooklm_pipeline.stages.generate import run_generate
from obsidian_notebooklm_pipeline.stages.pack import run_pack
from obsidian_notebooklm_pipeline.stages.publish import run_publish
from obsidian_notebooklm_pipeline.stages.sync import run_sync


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the narrow Obsidian -> NotebookLM scaffold")
    subparsers = parser.add_subparsers(dest="command", required=True)

    reading_map_run_parser = subparsers.add_parser("reading-map-run")
    reading_map_run_parser.add_argument("--corpus-dir", type=Path, required=True)
    reading_map_run_parser.add_argument("--work-dir", type=Path, required=True)
    reading_map_run_parser.add_argument("--reading-map", type=Path, required=True)
    reading_map_run_parser.add_argument("--recipes", type=Path)
    reading_map_run_parser.add_argument("--source-ids", type=Path)
    reading_map_run_parser.add_argument("--notebook-id")
    reading_map_run_parser.add_argument("--profile")
    reading_map_run_parser.add_argument("--execute-generate", action="store_true")
    reading_map_run_parser.add_argument("--downloads-dir", type=Path)
    reading_map_run_parser.add_argument("--output-dir", type=Path)

    pack_parser = subparsers.add_parser("pack")
    pack_parser.add_argument("--corpus-dir", type=Path, required=True)
    pack_parser.add_argument("--work-dir", type=Path, required=True)
    pack_parser.add_argument("--reading-map", type=Path)

    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--work-dir", type=Path, required=True)
    sync_parser.add_argument("--source-ids", type=Path)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--work-dir", type=Path, required=True)
    generate_parser.add_argument("--recipes", type=Path)
    generate_parser.add_argument("--notebook-id")
    generate_parser.add_argument("--profile")
    generate_parser.add_argument("--execute", action="store_true")

    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument("--work-dir", type=Path, required=True)
    publish_parser.add_argument("--downloads-dir", type=Path)
    publish_parser.add_argument("--output-dir", type=Path)

    all_parser = subparsers.add_parser("all")
    all_parser.add_argument("--corpus-dir", type=Path, required=True)
    all_parser.add_argument("--work-dir", type=Path, required=True)
    all_parser.add_argument("--reading-map", type=Path)
    all_parser.add_argument("--source-ids", type=Path)
    all_parser.add_argument("--recipes", type=Path)
    all_parser.add_argument("--notebook-id")
    all_parser.add_argument("--profile")
    all_parser.add_argument("--execute-generate", action="store_true")
    all_parser.add_argument("--downloads-dir", type=Path)
    all_parser.add_argument("--output-dir", type=Path)

    return parser


def print_json(payload: dict | list) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _resolve_if_exists(path: Path | None, default_path: Path) -> Path | None:
    if path is not None:
        return path
    if default_path.exists():
        return default_path
    return None


def _build_reading_map_run_summary(
    *,
    work_dir: Path,
    corpus_dir: Path,
    reading_map_path: Path,
    recipes_path: Path | None,
    source_ids_path: Path | None,
    notebook_id: str | None,
    profile: str | None,
    execute_generate: bool,
    downloads_dir: Path | None,
    output_dir: Path | None,
) -> dict[str, Any]:
    default_source_ids_path = work_dir / "manual_source_updates.json"
    default_downloads_dir = work_dir / "downloads"
    default_output_dir = output_dir or (work_dir / "outputs")

    resolved_source_ids_path = _resolve_if_exists(source_ids_path, default_source_ids_path)
    resolved_downloads_dir = _resolve_if_exists(downloads_dir, default_downloads_dir)

    pack_result = run_pack(corpus_dir, work_dir, reading_map_path)
    source_map = run_sync(work_dir, resolved_source_ids_path)
    generate_result = run_generate(
        work_dir,
        recipes_path,
        notebook_id=notebook_id,
        profile=profile,
        execute=execute_generate,
    )

    publish_result = None
    if resolved_downloads_dir is not None:
        publish_result = run_publish(work_dir, resolved_downloads_dir, output_dir)

    pending_segment_ids = [entry.segment_id for entry in source_map.entries if entry.sync_status != "synced"]
    blocked_recipe_names = [
        request.recipe.name
        for request in generate_result.request.recipe_requests
        if request.guard_status == "blocked"
    ]
    ready_recipe_names = [
        request.recipe.name
        for request in generate_result.request.recipe_requests
        if request.guard_status == "ready"
    ]

    if pending_segment_ids:
        next_action = (
            f"Sync pending segments in NotebookLM, write updates to {resolved_source_ids_path or default_source_ids_path}, "
            "then rerun reading-map-run."
        )
    elif notebook_id is None:
        next_action = "Add --notebook-id to turn the generation request into concrete nlm commands."
    elif blocked_recipe_names:
        next_action = "Fix the blocked recipes described in generation_request.json, then rerun reading-map-run."
    elif not execute_generate:
        next_action = "Review generation_request.json, then rerun with --execute-generate when ready to call nlm."
    elif publish_result is None:
        next_action = (
            f"Download the created artifacts into {resolved_downloads_dir or default_downloads_dir}, then rerun "
            "reading-map-run to publish them locally."
        )
    elif any(artifact.status != "published" for artifact in publish_result.artifacts):
        next_action = "Resolve missing or ambiguous downloads in publish_manifest.json, then rerun reading-map-run."
    else:
        next_action = "Reading-map-first run is locally complete; review outputs/ and recorded artifacts in the work dir."

    if pending_segment_ids:
        source_sync_status = "manual_sync_required"
    else:
        source_sync_status = "synced"

    if blocked_recipe_names:
        generation_status = "blocked"
    elif execute_generate and generate_result.run is not None:
        generation_status = "executed"
    elif ready_recipe_names:
        generation_status = "ready_to_execute"
    else:
        generation_status = "awaiting_notebook_id"

    if publish_result is None:
        publish_status = "awaiting_downloads"
    elif any(artifact.status == "ambiguous" for artifact in publish_result.artifacts):
        publish_status = "ambiguous"
    elif any(artifact.status == "missing" for artifact in publish_result.artifacts):
        publish_status = "missing"
    else:
        publish_status = "published"

    return {
        "entrypoint": "reading-map-run",
        "mode": "reading_map_first",
        "work_dir": str(work_dir),
        "corpus_dir": str(corpus_dir),
        "reading_map_path": str(reading_map_path),
        "recipes_path": str(recipes_path) if recipes_path else None,
        "notebook_id": notebook_id,
        "profile": profile,
        "artifacts": {
            "source_pack_path": str(work_dir / "source_pack.json"),
            "source_map_path": str(work_dir / "source_map.json"),
            "source_drift_path": str(work_dir / "source_drift.json"),
            "sync_handoff_path": str(work_dir / "sync_handoff.json"),
            "generation_request_path": str(work_dir / "generation_request.json"),
            "generation_run_path": str(work_dir / "generation_run.json") if generate_result.run else None,
            "publish_manifest_path": str(work_dir / "publish_manifest.json") if publish_result else None,
            "run_metadata_path": str(work_dir / "run_metadata.json"),
            "downloads_dir": str(resolved_downloads_dir or default_downloads_dir),
            "output_dir": str(default_output_dir),
            "manual_source_updates_path": str(resolved_source_ids_path or default_source_ids_path),
        },
        "manual_boundaries": {
            "source_sync": {
                "status": source_sync_status,
                "pending_segment_ids": pending_segment_ids,
                "sync_handoff_path": str(work_dir / "sync_handoff.json"),
                "manual_source_updates_path": str(resolved_source_ids_path or default_source_ids_path),
                "manual_source_updates_provided": resolved_source_ids_path is not None,
            },
            "generation": {
                "status": generation_status,
                "blocked_recipe_names": blocked_recipe_names,
                "ready_recipe_names": ready_recipe_names,
                "generation_request_path": str(work_dir / "generation_request.json"),
                "generation_run_path": str(work_dir / "generation_run.json") if generate_result.run else None,
                "execute_requested": execute_generate,
            },
            "publish": {
                "status": publish_status,
                "downloads_dir": str(resolved_downloads_dir or default_downloads_dir),
                "publish_manifest_path": str(work_dir / "publish_manifest.json") if publish_result else None,
            },
        },
        "next_action": next_action,
        "stage_results": {
            "pack": pack_result.to_dict(),
            "sync": source_map.to_dict(),
            "generate": generate_result.to_dict(),
            "publish": publish_result.to_dict() if publish_result else None,
        },
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "reading-map-run":
        print_json(
            _build_reading_map_run_summary(
                work_dir=args.work_dir,
                corpus_dir=args.corpus_dir,
                reading_map_path=args.reading_map,
                recipes_path=args.recipes,
                source_ids_path=args.source_ids,
                notebook_id=args.notebook_id,
                profile=args.profile,
                execute_generate=args.execute_generate,
                downloads_dir=args.downloads_dir,
                output_dir=args.output_dir,
            )
        )
        return 0

    if args.command == "pack":
        print_json(run_pack(args.corpus_dir, args.work_dir, args.reading_map).to_dict())
        return 0

    if args.command == "sync":
        print_json(run_sync(args.work_dir, args.source_ids).to_dict())
        return 0

    if args.command == "generate":
        print_json(
            run_generate(
                args.work_dir,
                args.recipes,
                notebook_id=args.notebook_id,
                profile=args.profile,
                execute=args.execute,
            ).to_dict()
        )
        return 0

    if args.command == "publish":
        print_json(run_publish(args.work_dir, args.downloads_dir, args.output_dir).to_dict())
        return 0

    if args.command == "all":
        run_pack(args.corpus_dir, args.work_dir, args.reading_map)
        run_sync(args.work_dir, args.source_ids)
        run_generate(
            args.work_dir,
            args.recipes,
            notebook_id=args.notebook_id,
            profile=args.profile,
            execute=args.execute_generate,
        )
        print_json(run_publish(args.work_dir, args.downloads_dir, args.output_dir).to_dict())
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
