from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..io import (
    discover_markdown_files,
    first_heading_or_stem,
    now_utc,
    read_json,
    read_text,
    slugify_path,
    text_digest,
    write_json,
)
from ..models import Segment, SourcePack
from ..run_state import write_run_metadata, write_source_drift_report


@dataclass(frozen=True)
class ReadingMapEntry:
    source_path: str
    tags: tuple[str, ...] = ()


def _load_reading_map(reading_map_path: Path) -> list[ReadingMapEntry]:
    payload = read_json(reading_map_path)
    entries = payload.get("segments")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Reading map must contain a non-empty 'segments' list")

    reading_map_entries: list[ReadingMapEntry] = []
    seen_paths: set[str] = set()

    for item in entries:
        source_path = item.get("source_path")
        tags = tuple(item.get("tags", []))
        if not isinstance(source_path, str) or not source_path:
            raise ValueError("Each reading-map segment must include 'source_path'")
        if source_path in seen_paths:
            raise ValueError(f"Reading map contains duplicate source_path: {source_path}")
        if not all(isinstance(tag, str) and tag for tag in tags):
            raise ValueError(f"Reading map tags must be non-empty strings: {source_path}")
        seen_paths.add(source_path)
        reading_map_entries.append(ReadingMapEntry(source_path=source_path, tags=tags))

    return reading_map_entries


def _selected_paths(corpus_dir: Path, reading_map_path: Path | None) -> list[ReadingMapEntry]:
    if reading_map_path is None:
        return [
            ReadingMapEntry(source_path=path.relative_to(corpus_dir).as_posix())
            for path in discover_markdown_files(corpus_dir)
        ]

    reading_map_entries = _load_reading_map(reading_map_path)
    resolved_entries: list[ReadingMapEntry] = []

    for entry in reading_map_entries:
        relative_path = Path(entry.source_path)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"Reading map source_path must stay inside the corpus: {entry.source_path}")
        absolute_path = corpus_dir / relative_path
        if relative_path.suffix.lower() != ".md":
            raise ValueError(f"Reading map source_path must point to a Markdown file: {entry.source_path}")
        if not absolute_path.is_file():
            raise FileNotFoundError(f"Reading map source_path not found in corpus: {entry.source_path}")
        resolved_entries.append(
            ReadingMapEntry(source_path=str(relative_path.as_posix()), tags=entry.tags)
        )

    return resolved_entries


def run_pack(corpus_dir: Path, work_dir: Path, reading_map_path: Path | None = None) -> SourcePack:
    """Build a source pack from the corpus or an explicit reading map."""
    selected_entries = _selected_paths(corpus_dir, reading_map_path)
    segments: list[Segment] = []

    for order, entry in enumerate(selected_entries):
        relative_path = Path(entry.source_path)
        text = read_text(corpus_dir / relative_path)
        segments.append(
            Segment(
                segment_id=slugify_path(str(relative_path.with_suffix(""))),
                title=first_heading_or_stem(text, fallback=relative_path.stem),
                source_path=str(relative_path.as_posix()),
                text=text,
                text_digest=text_digest(text),
                order=order,
                tags=entry.tags,
            )
        )

    source_pack = SourcePack(
        corpus_id=corpus_dir.name,
        generated_at=now_utc(),
        selection_mode="reading_map" if reading_map_path else "scan",
        reading_map_path=str(reading_map_path) if reading_map_path else None,
        segments=segments,
    )
    write_json(work_dir / "source_pack.json", source_pack.to_dict())
    write_source_drift_report(work_dir, source_pack=source_pack)
    write_run_metadata(work_dir)
    return source_pack
