from __future__ import annotations

import shutil
from pathlib import Path

from ..io import ensure_dir, read_json, write_json
from ..models import GenerationRequest, PublishedArtifact
from ..recipes import expected_artifact_name


def run_publish(
    work_dir: Path,
    downloads_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[PublishedArtifact]:
    """Copy any manually downloaded artifacts into stable local output folders."""
    downloads_dir = downloads_dir or (work_dir / "downloads")
    output_dir = output_dir or (work_dir / "outputs")

    request = GenerationRequest.from_dict(read_json(work_dir / "generation_request.json"))
    published: list[PublishedArtifact] = []

    for recipe_request in request.recipe_requests:
        recipe = recipe_request.recipe
        source_path = downloads_dir / expected_artifact_name(recipe)
        destination_dir = ensure_dir(output_dir / recipe.artifact_kind)
        destination_path = destination_dir / source_path.name

        if source_path.exists():
            shutil.copy2(source_path, destination_path)
            artifact = PublishedArtifact(
                recipe_name=recipe.name,
                artifact_kind=recipe.artifact_kind,
                source_path=str(source_path),
                output_path=str(destination_path),
                status="published",
            )
        else:
            artifact = PublishedArtifact(
                recipe_name=recipe.name,
                artifact_kind=recipe.artifact_kind,
                source_path=str(source_path),
                output_path=None,
                status="missing",
            )

        published.append(artifact)

    write_json(work_dir / "publish_manifest.json", [artifact.to_dict() for artifact in published])
    return published
