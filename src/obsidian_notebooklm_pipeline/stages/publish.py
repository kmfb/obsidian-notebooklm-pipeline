from __future__ import annotations

import shutil
from pathlib import Path

from ..io import ensure_dir, now_utc, read_json, write_json
from ..models import GenerationRequest, PublishManifest, PublishedArtifact
from ..recipes import expected_artifact_name
from ..run_state import write_run_metadata


def _find_download_candidates(downloads_dir: Path, expected_name: str) -> list[Path]:
    if not downloads_dir.exists():
        return []
    return sorted(path for path in downloads_dir.rglob(expected_name) if path.is_file())


def run_publish(
    work_dir: Path,
    downloads_dir: Path | None = None,
    output_dir: Path | None = None,
) -> PublishManifest:
    """Copy any manually downloaded artifacts into stable local output folders."""
    downloads_dir = downloads_dir or (work_dir / "downloads")
    output_dir = output_dir or (work_dir / "outputs")

    request_path = work_dir / "generation_request.json"
    request = GenerationRequest.from_dict(read_json(request_path))
    published: list[PublishedArtifact] = []

    for recipe_request in request.recipe_requests:
        recipe = recipe_request.recipe
        expected_name = expected_artifact_name(recipe)
        candidates = _find_download_candidates(downloads_dir, expected_name)
        destination_dir = ensure_dir(output_dir / recipe.artifact_kind)
        destination_path = destination_dir / expected_name

        if len(candidates) == 1:
            source_path = candidates[0]
            shutil.copy2(source_path, destination_path)
            artifact = PublishedArtifact(
                recipe_name=recipe.name,
                artifact_kind=recipe.artifact_kind,
                source_path=str(source_path),
                output_path=str(destination_path),
                status="published",
                intake_candidates=[str(source_path)],
            )
        elif len(candidates) > 1:
            artifact = PublishedArtifact(
                recipe_name=recipe.name,
                artifact_kind=recipe.artifact_kind,
                source_path=None,
                output_path=None,
                status="ambiguous",
                intake_candidates=[str(path) for path in candidates],
            )
        else:
            artifact = PublishedArtifact(
                recipe_name=recipe.name,
                artifact_kind=recipe.artifact_kind,
                source_path=str(downloads_dir / expected_name),
                output_path=None,
                status="missing",
                intake_candidates=[],
            )

        published.append(artifact)

    publish_manifest = PublishManifest(
        published_at=now_utc(),
        generation_request_path=str(request_path),
        downloads_dir=str(downloads_dir),
        output_dir=str(output_dir),
        artifacts=published,
    )
    write_json(work_dir / "publish_manifest.json", publish_manifest.to_dict())
    write_run_metadata(work_dir)
    return publish_manifest
