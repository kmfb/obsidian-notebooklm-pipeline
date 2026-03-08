#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
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
    all_parser.add_argument("--downloads-dir", type=Path)
    all_parser.add_argument("--output-dir", type=Path)

    return parser


def print_json(payload: dict | list) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "pack":
        print_json(run_pack(args.corpus_dir, args.work_dir, args.reading_map).to_dict())
        return 0

    if args.command == "sync":
        print_json(run_sync(args.work_dir, args.source_ids).to_dict())
        return 0

    if args.command == "generate":
        print_json(run_generate(args.work_dir, args.recipes).to_dict())
        return 0

    if args.command == "publish":
        print_json([artifact.to_dict() for artifact in run_publish(args.work_dir, args.downloads_dir, args.output_dir)])
        return 0

    if args.command == "all":
        run_pack(args.corpus_dir, args.work_dir, args.reading_map)
        run_sync(args.work_dir, args.source_ids)
        run_generate(args.work_dir, args.recipes)
        print_json([artifact.to_dict() for artifact in run_publish(args.work_dir, args.downloads_dir, args.output_dir)])
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
