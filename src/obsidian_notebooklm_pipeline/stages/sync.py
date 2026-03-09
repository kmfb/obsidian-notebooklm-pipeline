from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..io import now_utc, read_json, write_json
from ..models import SourceMap, SourceMapEntry, SourcePack
from ..run_state import write_run_metadata, write_source_drift_report


@dataclass(frozen=True)
class SyncUpdate:
    segment_id: str
    notebooklm_source_id: str | None


@dataclass(frozen=True)
class SyncHandoffEntry:
    segment_id: str
    source_path: str
    title: str
    sync_status: str
    notebooklm_source_id: str | None

    def to_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "source_path": self.source_path,
            "title": self.title,
            "sync_status": self.sync_status,
            "notebooklm_source_id": self.notebooklm_source_id,
        }


def _load_existing_source_map(source_map_path: Path) -> SourceMap | None:
    if not source_map_path.exists():
        return None
    return SourceMap.from_dict(read_json(source_map_path))


def _load_sync_updates(source_ids_path: Path | None) -> dict[str, SyncUpdate]:
    if source_ids_path is None:
        return {}

    payload = read_json(source_ids_path)
    updates = payload.get("updates")
    if not isinstance(updates, list):
        raise ValueError("Sync update file must contain an 'updates' list")

    parsed_updates: dict[str, SyncUpdate] = {}
    for item in updates:
        segment_id = item.get("segment_id")
        notebooklm_source_id = item.get("notebooklm_source_id")
        if not isinstance(segment_id, str) or not segment_id:
            raise ValueError("Each sync update must include a non-empty 'segment_id'")
        if notebooklm_source_id is not None and not isinstance(notebooklm_source_id, str):
            raise ValueError(f"Invalid notebooklm_source_id for segment: {segment_id}")
        if segment_id in parsed_updates:
            raise ValueError(f"Duplicate sync update for segment: {segment_id}")
        parsed_updates[segment_id] = SyncUpdate(
            segment_id=segment_id,
            notebooklm_source_id=notebooklm_source_id,
        )

    return parsed_updates


def _write_sync_handoff(
    work_dir: Path,
    source_pack_path: Path,
    source_ids_path: Path | None,
    source_map: SourceMap,
) -> None:
    pending_segments: list[SyncHandoffEntry] = []
    synced_segments: list[SyncHandoffEntry] = []

    for entry in source_map.entries:
        handoff_entry = SyncHandoffEntry(
            segment_id=entry.segment_id,
            source_path=entry.source_path,
            title=entry.title,
            sync_status=entry.sync_status,
            notebooklm_source_id=entry.notebooklm_source_id,
        )
        if entry.sync_status == "synced":
            synced_segments.append(handoff_entry)
        else:
            pending_segments.append(handoff_entry)

    write_json(
        work_dir / "sync_handoff.json",
        {
            "corpus_id": source_map.corpus_id,
            "updated_at": source_map.updated_at,
            "source_pack_path": str(source_pack_path),
            "source_map_path": str(work_dir / "source_map.json"),
            "manual_updates_path": str(source_ids_path) if source_ids_path else None,
            "manual_updates_format": {
                "updates": [
                    {
                        "segment_id": "segment-id",
                        "notebooklm_source_id": "notebooklm-source-id-or-null",
                    }
                ]
            },
            "pending_segments": [entry.to_dict() for entry in pending_segments],
            "synced_segments": [entry.to_dict() for entry in synced_segments],
        },
    )


def run_sync(work_dir: Path, source_ids_path: Path | None = None) -> SourceMap:
    """Persist explicit segment sync state from manual sync updates."""
    source_pack_path = work_dir / "source_pack.json"
    source_map_path = work_dir / "source_map.json"
    source_pack = SourcePack.from_dict(read_json(source_pack_path))
    existing_source_map = _load_existing_source_map(source_map_path)
    if existing_source_map and existing_source_map.corpus_id != source_pack.corpus_id:
        raise ValueError("Existing source_map.json belongs to a different corpus")

    sync_updates = _load_sync_updates(source_ids_path)
    source_pack_segment_ids = {segment.segment_id for segment in source_pack.segments}
    unknown_segment_ids = sorted(set(sync_updates) - source_pack_segment_ids)
    if unknown_segment_ids:
        raise ValueError(f"Sync updates reference unknown segment_id values: {', '.join(unknown_segment_ids)}")

    existing_entries = {
        entry.segment_id: entry for entry in (existing_source_map.entries if existing_source_map else [])
    }
    updated_at = now_utc()
    entries: list[SourceMapEntry] = []

    for segment in source_pack.segments:
        existing_entry = existing_entries.get(segment.segment_id)
        sync_update = sync_updates.get(segment.segment_id)

        if sync_update is not None:
            notebooklm_source_id = sync_update.notebooklm_source_id
            synced_at = updated_at if notebooklm_source_id else None
        elif existing_entry is not None:
            notebooklm_source_id = existing_entry.notebooklm_source_id
            synced_at = existing_entry.synced_at
        else:
            notebooklm_source_id = None
            synced_at = None

        entries.append(
            SourceMapEntry(
                segment_id=segment.segment_id,
                source_path=segment.source_path,
                title=segment.title,
                text_digest=segment.text_digest,
                notebooklm_source_id=notebooklm_source_id,
                sync_status="synced" if notebooklm_source_id else "pending",
                synced_at=synced_at,
            )
        )

    source_map = SourceMap(
        corpus_id=source_pack.corpus_id,
        updated_at=updated_at,
        entries=entries,
    )
    write_json(source_map_path, source_map.to_dict())
    _write_sync_handoff(work_dir, source_pack_path, source_ids_path, source_map)
    write_source_drift_report(work_dir, source_pack=source_pack, source_map=source_map)
    write_run_metadata(work_dir)
    return source_map
