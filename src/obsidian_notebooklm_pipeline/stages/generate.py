from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from ..io import now_utc, read_json, write_json
from ..models import (
    GenerateStageResult,
    GenerationRequest,
    GenerationRun,
    Recipe,
    RecipeGenerationRequest,
    RecipeGenerationResult,
    SourceMap,
)
from ..recipes import load_recipes

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _build_command(
    recipe: Recipe,
    notebook_id: str,
    profile: str | None,
    source_ids: list[str],
) -> list[str]:
    command = ["nlm", recipe.artifact_kind, "create", notebook_id]

    if recipe.format is not None:
        command.extend(["--format", recipe.format])
    if recipe.length is not None:
        command.extend(["--length", recipe.length])
    if recipe.language is not None:
        command.extend(["--language", recipe.language])
    if recipe.focus is not None:
        command.extend(["--focus", recipe.focus])
    if recipe.prompt is not None:
        command.extend(["--prompt", recipe.prompt])
    if source_ids:
        command.extend(["--source-ids", ",".join(source_ids)])

    command.append("--confirm")
    if profile is not None:
        command.extend(["--profile", profile])

    return command


def _build_recipe_request(
    recipe: Recipe,
    notebook_id: str | None,
    profile: str | None,
    unsynced_segment_ids: list[str],
    synced_entries_by_source_id: dict[str, tuple[str, str]],
    all_synced_source_ids: list[str],
) -> RecipeGenerationRequest:
    blocked_reasons: list[str] = []

    if recipe.source_ids:
        requested_source_ids = list(recipe.source_ids)
        missing_source_ids = [
            source_id for source_id in requested_source_ids if source_id not in synced_entries_by_source_id
        ]
        if missing_source_ids:
            blocked_reasons.append(
                "recipe references source_ids that are not synced in source_map.json: "
                + ", ".join(missing_source_ids)
            )
        effective_source_ids = [
            source_id for source_id in requested_source_ids if source_id in synced_entries_by_source_id
        ]
    else:
        effective_source_ids = list(all_synced_source_ids)
        if unsynced_segment_ids:
            blocked_reasons.append(
                "recipe does not pin source_ids and source_map.json still has pending segments: "
                + ", ".join(unsynced_segment_ids)
            )

    if not effective_source_ids:
        blocked_reasons.append("recipe resolved to zero synced source_ids")
    if notebook_id is None:
        blocked_reasons.append("notebook_id is required before guarded generation can call nlm")

    source_segment_ids = [synced_entries_by_source_id[source_id][0] for source_id in effective_source_ids]
    source_paths = [synced_entries_by_source_id[source_id][1] for source_id in effective_source_ids]
    command = (
        _build_command(recipe, notebook_id, profile, effective_source_ids)
        if notebook_id is not None
        else []
    )

    return RecipeGenerationRequest(
        recipe=recipe,
        source_ids=effective_source_ids,
        source_segment_ids=source_segment_ids,
        source_paths=source_paths,
        command=command,
        guard_status="blocked" if blocked_reasons else "ready",
        blocked_reasons=blocked_reasons,
    )


def _assemble_generation_request(
    work_dir: Path,
    source_map: SourceMap,
    recipes: list[Recipe],
    recipes_path: Path | None,
    notebook_id: str | None,
    profile: str | None,
) -> GenerationRequest:
    unsynced_segment_ids = [
        entry.segment_id for entry in source_map.entries if entry.sync_status != "synced"
    ]
    synced_entries = [entry for entry in source_map.entries if entry.notebooklm_source_id]
    synced_entries_by_source_id = {
        entry.notebooklm_source_id: (entry.segment_id, entry.source_path)
        for entry in synced_entries
        if entry.notebooklm_source_id is not None
    }
    all_synced_source_ids = list(synced_entries_by_source_id)

    return GenerationRequest(
        run_id=uuid4().hex[:12],
        created_at=now_utc(),
        corpus_id=source_map.corpus_id,
        source_map_path=str(work_dir / "source_map.json"),
        recipes_path=str(recipes_path) if recipes_path else None,
        notebook_id=notebook_id,
        profile=profile,
        unsynced_segment_ids=unsynced_segment_ids,
        synced_source_ids=all_synced_source_ids,
        recipe_requests=[
            _build_recipe_request(
                recipe=recipe,
                notebook_id=notebook_id,
                profile=profile,
                unsynced_segment_ids=unsynced_segment_ids,
                synced_entries_by_source_id=synced_entries_by_source_id,
                all_synced_source_ids=all_synced_source_ids,
            )
            for recipe in recipes
        ],
    )


def _default_command_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)



def run_guarded_generation(
    work_dir: Path,
    runner: CommandRunner | None = None,
) -> GenerationRun:
    request_path = work_dir / "generation_request.json"
    request = GenerationRequest.from_dict(read_json(request_path))
    runner = runner or _default_command_runner

    results: list[RecipeGenerationResult] = []
    for recipe_request in request.recipe_requests:
        if recipe_request.guard_status == "blocked":
            results.append(
                RecipeGenerationResult(
                    recipe_name=recipe_request.recipe.name,
                    artifact_kind=recipe_request.recipe.artifact_kind,
                    command=recipe_request.command,
                    status="blocked",
                    stderr="; ".join(recipe_request.blocked_reasons),
                )
            )
            continue

        completed = runner(recipe_request.command)
        results.append(
            RecipeGenerationResult(
                recipe_name=recipe_request.recipe.name,
                artifact_kind=recipe_request.recipe.artifact_kind,
                command=recipe_request.command,
                status="created" if completed.returncode == 0 else "failed",
                exit_code=completed.returncode,
                stdout=completed.stdout.strip() or None,
                stderr=completed.stderr.strip() or None,
            )
        )

    generation_run = GenerationRun(
        run_id=request.run_id,
        executed_at=now_utc(),
        request_path=str(request_path),
        results=results,
    )
    write_json(work_dir / "generation_run.json", generation_run.to_dict())
    return generation_run



def run_generate(
    work_dir: Path,
    recipes_path: Path | None = None,
    notebook_id: str | None = None,
    profile: str | None = None,
    execute: bool = False,
    runner: CommandRunner | None = None,
) -> GenerateStageResult:
    """Create a file-backed generation request and optionally run guarded nlm commands."""
    source_map = SourceMap.from_dict(read_json(work_dir / "source_map.json"))
    recipes = load_recipes(recipes_path)
    generation_request = _assemble_generation_request(
        work_dir=work_dir,
        source_map=source_map,
        recipes=recipes,
        recipes_path=recipes_path,
        notebook_id=notebook_id,
        profile=profile,
    )
    write_json(work_dir / "generation_request.json", generation_request.to_dict())

    generation_run = run_guarded_generation(work_dir, runner=runner) if execute else None
    return GenerateStageResult(request=generation_request, run=generation_run)
