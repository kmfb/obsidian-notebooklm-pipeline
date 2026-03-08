from __future__ import annotations

from pathlib import Path

from ..io import now_utc, read_json, write_json
from ..models import SourceMap, SourceMapEntry, SourcePack


def run_sync(work_dir: Path, source_ids_path: Path | None = None) -> SourceMap:
    """Persist explicit sync state without pretending NotebookLM automation exists.

    If `source_ids_path` is provided, it must contain a JSON object mapping local
    `segment_id` values to NotebookLM source IDs. Missing mappings stay pending.
    """
    source_pack = SourcePack.from_dict(read_json(work_dir / "source_pack.json"))
    manual_mapping = read_json(source_ids_path) if source_ids_path else {}

    source_map = SourceMap(
        corpus_id=source_pack.corpus_id,
        updated_at=now_utc(),
        entries=[
            SourceMapEntry(
                segment_id=segment.segment_id,
                notebooklm_source_id=manual_mapping.get(segment.segment_id),
                sync_status="synced" if manual_mapping.get(segment.segment_id) else "pending",
            )
            for segment in source_pack.segments
        ],
    )
    write_json(work_dir / "source_map.json", source_map.to_dict())
    return source_map
