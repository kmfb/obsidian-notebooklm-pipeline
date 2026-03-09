from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import now_utc, read_json, write_json
from .models import (
    DriftedSegment,
    PublishManifest,
    SegmentReference,
    SourceDriftReport,
    SourceMap,
    SourcePack,
)


def _read_optional_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return read_json(path)


def _segment_reference_from_pack(segment) -> SegmentReference:
    return SegmentReference(
        segment_id=segment.segment_id,
        source_path=segment.source_path,
        title=segment.title,
    )


def _segment_reference_from_map(entry) -> SegmentReference:
    return SegmentReference(
        segment_id=entry.segment_id,
        source_path=entry.source_path,
        title=entry.title,
    )


def build_source_drift_report(
    work_dir: Path,
    *,
    source_pack: SourcePack | None = None,
    source_map: SourceMap | None = None,
) -> SourceDriftReport:
    source_pack_path = work_dir / "source_pack.json"
    source_map_path = work_dir / "source_map.json"
    source_pack = source_pack or SourcePack.from_dict(read_json(source_pack_path))

    if source_map is None:
        source_map_payload = _read_optional_json(source_map_path)
        if source_map_payload is None:
            return SourceDriftReport(
                status="source_map_missing",
                checked_at=now_utc(),
                source_pack_path=str(source_pack_path),
                source_map_path=str(source_map_path),
            )
        source_map = SourceMap.from_dict(source_map_payload)

    pack_segments = {segment.segment_id: segment for segment in source_pack.segments}
    map_entries = {entry.segment_id: entry for entry in source_map.entries}

    changed_segments: list[DriftedSegment] = []
    missing_segments: list[SegmentReference] = []
    extra_segments: list[SegmentReference] = []

    for segment_id in sorted(pack_segments):
        segment = pack_segments[segment_id]
        entry = map_entries.get(segment_id)
        if entry is None:
            missing_segments.append(_segment_reference_from_pack(segment))
            continue

        reasons: list[str] = []
        if entry.source_path != segment.source_path:
            reasons.append("source_path changed")
        if entry.title != segment.title:
            reasons.append("title changed")
        if entry.text_digest != segment.text_digest:
            reasons.append("text_digest changed")

        if reasons:
            changed_segments.append(
                DriftedSegment(
                    segment_id=segment.segment_id,
                    source_path=segment.source_path,
                    title=segment.title,
                    reasons=tuple(reasons),
                )
            )

    for segment_id in sorted(map_entries):
        if segment_id not in pack_segments:
            extra_segments.append(_segment_reference_from_map(map_entries[segment_id]))

    drifted_segment_ids = sorted(
        {
            *(segment.segment_id for segment in changed_segments),
            *(segment.segment_id for segment in missing_segments),
            *(segment.segment_id for segment in extra_segments),
        }
    )

    return SourceDriftReport(
        status="drifted" if drifted_segment_ids else "clean",
        checked_at=now_utc(),
        source_pack_path=str(source_pack_path),
        source_map_path=str(source_map_path),
        changed_segments=changed_segments,
        missing_segments=missing_segments,
        extra_segments=extra_segments,
        drifted_segment_ids=drifted_segment_ids,
    )


def write_source_drift_report(
    work_dir: Path,
    *,
    source_pack: SourcePack | None = None,
    source_map: SourceMap | None = None,
) -> SourceDriftReport:
    report = build_source_drift_report(work_dir, source_pack=source_pack, source_map=source_map)
    write_json(work_dir / "source_drift.json", report.to_dict())
    return report


def write_run_metadata(work_dir: Path) -> dict[str, Any]:
    source_pack_payload = _read_optional_json(work_dir / "source_pack.json")
    source_map_payload = _read_optional_json(work_dir / "source_map.json")
    source_drift_payload = _read_optional_json(work_dir / "source_drift.json")
    generation_request_payload = _read_optional_json(work_dir / "generation_request.json")
    generation_run_payload = _read_optional_json(work_dir / "generation_run.json")
    publish_manifest_payload = _read_optional_json(work_dir / "publish_manifest.json")

    metadata: dict[str, Any] = {
        "updated_at": now_utc(),
        "corpus_id": None,
        "source_pack": None,
        "source_map": None,
        "source_drift": None,
        "generation_request": None,
        "generation_run": None,
        "publish_manifest": None,
    }

    if source_pack_payload is not None:
        source_pack = SourcePack.from_dict(source_pack_payload)
        metadata["corpus_id"] = source_pack.corpus_id
        metadata["source_pack"] = {
            "path": str(work_dir / "source_pack.json"),
            "generated_at": source_pack.generated_at,
            "selection_mode": source_pack.selection_mode,
            "reading_map_path": source_pack.reading_map_path,
            "segment_count": len(source_pack.segments),
        }

    if source_map_payload is not None:
        source_map = SourceMap.from_dict(source_map_payload)
        metadata["corpus_id"] = metadata["corpus_id"] or source_map.corpus_id
        metadata["source_map"] = {
            "path": str(work_dir / "source_map.json"),
            "updated_at": source_map.updated_at,
            "entry_count": len(source_map.entries),
            "pending_segment_ids": [entry.segment_id for entry in source_map.entries if entry.sync_status != "synced"],
            "synced_segment_ids": [entry.segment_id for entry in source_map.entries if entry.sync_status == "synced"],
        }

    if source_drift_payload is not None:
        source_drift = SourceDriftReport.from_dict(source_drift_payload)
        metadata["source_drift"] = {
            "path": str(work_dir / "source_drift.json"),
            "status": source_drift.status,
            "drifted_segment_ids": list(source_drift.drifted_segment_ids),
            "changed_count": len(source_drift.changed_segments),
            "missing_count": len(source_drift.missing_segments),
            "extra_count": len(source_drift.extra_segments),
        }

    if generation_request_payload is not None:
        blocked_recipe_names = [
            request["recipe"]["name"]
            for request in generation_request_payload.get("recipe_requests", [])
            if request.get("guard_status") == "blocked"
        ]
        metadata["generation_request"] = {
            "path": str(work_dir / "generation_request.json"),
            "run_id": generation_request_payload["run_id"],
            "created_at": generation_request_payload["created_at"],
            "recipes_path": generation_request_payload.get("recipes_path"),
            "notebook_id": generation_request_payload.get("notebook_id"),
            "profile": generation_request_payload.get("profile"),
            "recipe_count": len(generation_request_payload.get("recipe_requests", [])),
            "blocked_recipe_names": blocked_recipe_names,
            "source_drift_status": generation_request_payload.get("source_drift_status"),
        }

    if generation_run_payload is not None:
        metadata["generation_run"] = {
            "path": str(work_dir / "generation_run.json"),
            "run_id": generation_run_payload["run_id"],
            "executed_at": generation_run_payload["executed_at"],
            "result_statuses": {
                result["recipe_name"]: result["status"]
                for result in generation_run_payload.get("results", [])
            },
        }

    if publish_manifest_payload is not None:
        publish_manifest = PublishManifest.from_dict(publish_manifest_payload)
        artifacts_by_status: dict[str, list[str]] = {
            "published": [],
            "missing": [],
            "ambiguous": [],
        }
        for artifact in publish_manifest.artifacts:
            artifacts_by_status.setdefault(artifact.status, []).append(artifact.recipe_name)
        metadata["publish_manifest"] = {
            "path": str(work_dir / "publish_manifest.json"),
            "published_at": publish_manifest.published_at,
            "downloads_dir": publish_manifest.downloads_dir,
            "output_dir": publish_manifest.output_dir,
            "artifacts_by_status": artifacts_by_status,
        }

    write_json(work_dir / "run_metadata.json", metadata)
    return metadata
