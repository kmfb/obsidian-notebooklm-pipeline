from __future__ import annotations

from pathlib import Path

from ..io import discover_markdown_files, first_heading_or_stem, now_utc, read_text, slugify_path, write_json
from ..models import Segment, SourcePack


def run_pack(corpus_dir: Path, work_dir: Path, reading_map_path: Path | None = None) -> SourcePack:
    """Build a minimal source pack.

    Phase 1 scaffold behavior is intentionally narrow: every Markdown file under
    `corpus_dir` becomes one segment. `reading_map_path` is accepted so the stage
    boundary is visible now, but it is not implemented yet.
    """
    markdown_files = discover_markdown_files(corpus_dir)
    segments: list[Segment] = []

    for order, path in enumerate(markdown_files):
        relative_path = path.relative_to(corpus_dir)
        text = read_text(path)
        segments.append(
            Segment(
                segment_id=slugify_path(str(relative_path.with_suffix(""))),
                title=first_heading_or_stem(text, fallback=path.stem),
                source_path=str(relative_path),
                text=text,
                order=order,
            )
        )

    source_pack = SourcePack(
        corpus_id=corpus_dir.name,
        generated_at=now_utc(),
        segments=segments,
    )
    write_json(work_dir / "source_pack.json", source_pack.to_dict())
    return source_pack
