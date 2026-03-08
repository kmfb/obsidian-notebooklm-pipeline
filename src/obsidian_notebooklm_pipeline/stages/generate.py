from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ..io import now_utc, read_json, write_json
from ..models import GenerationRequest, SourceMap
from ..recipes import load_recipes


def run_generate(work_dir: Path, recipes_path: Path | None = None) -> GenerationRequest:
    """Create a file-backed generation request for later NotebookLM work."""
    source_map = SourceMap.from_dict(read_json(work_dir / "source_map.json"))
    recipes = load_recipes(recipes_path)
    unsynced_segment_ids = [
        entry.segment_id for entry in source_map.entries if entry.sync_status != "synced"
    ]

    generation_request = GenerationRequest(
        run_id=uuid4().hex[:12],
        created_at=now_utc(),
        corpus_id=source_map.corpus_id,
        recipes=recipes,
        source_map_path=str(work_dir / "source_map.json"),
        recipes_path=str(recipes_path) if recipes_path else None,
        unsynced_segment_ids=unsynced_segment_ids,
    )
    write_json(work_dir / "generation_request.json", generation_request.to_dict())
    return generation_request
