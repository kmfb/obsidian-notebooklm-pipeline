from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

ArtifactKind = Literal["slides", "audio", "report"]
PackSelectionMode = Literal["scan", "reading_map"]
SyncStatus = Literal["pending", "synced"]
PublishStatus = Literal["missing", "published"]
GenerationGuardStatus = Literal["ready", "blocked"]
GenerationExecutionStatus = Literal["blocked", "created", "failed"]


@dataclass(frozen=True)
class Segment:
    segment_id: str
    title: str
    source_path: str
    text: str
    text_digest: str
    order: int
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourcePack:
    corpus_id: str
    generated_at: str
    selection_mode: PackSelectionMode
    reading_map_path: str | None
    segments: list[Segment]

    def to_dict(self) -> dict:
        return {
            "corpus_id": self.corpus_id,
            "generated_at": self.generated_at,
            "selection_mode": self.selection_mode,
            "reading_map_path": self.reading_map_path,
            "segments": [segment.to_dict() for segment in self.segments],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SourcePack":
        return cls(
            corpus_id=data["corpus_id"],
            generated_at=data["generated_at"],
            selection_mode=data["selection_mode"],
            reading_map_path=data.get("reading_map_path"),
            segments=[Segment(**segment) for segment in data["segments"]],
        )


@dataclass
class SourceMapEntry:
    segment_id: str
    source_path: str
    title: str
    text_digest: str
    notebooklm_source_id: str | None
    sync_status: SyncStatus
    synced_at: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourceMap:
    corpus_id: str
    updated_at: str
    entries: list[SourceMapEntry]

    def to_dict(self) -> dict:
        return {
            "corpus_id": self.corpus_id,
            "updated_at": self.updated_at,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SourceMap":
        return cls(
            corpus_id=data["corpus_id"],
            updated_at=data["updated_at"],
            entries=[SourceMapEntry(**entry) for entry in data["entries"]],
        )


@dataclass(frozen=True)
class Recipe:
    name: str
    artifact_kind: ArtifactKind
    language: str | None = None
    focus: str | None = None
    source_ids: tuple[str, ...] = ()
    format: str | None = None
    length: str | None = None
    prompt: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Recipe":
        return cls(
            name=data["name"],
            artifact_kind=data["artifact_kind"],
            language=data.get("language"),
            focus=data.get("focus"),
            source_ids=tuple(data.get("source_ids", [])),
            format=data.get("format"),
            length=data.get("length"),
            prompt=data.get("prompt"),
        )


@dataclass
class RecipeGenerationRequest:
    recipe: Recipe
    source_ids: list[str]
    source_segment_ids: list[str]
    source_paths: list[str]
    command: list[str]
    guard_status: GenerationGuardStatus
    blocked_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "recipe": self.recipe.to_dict(),
            "source_ids": list(self.source_ids),
            "source_segment_ids": list(self.source_segment_ids),
            "source_paths": list(self.source_paths),
            "command": list(self.command),
            "guard_status": self.guard_status,
            "blocked_reasons": list(self.blocked_reasons),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecipeGenerationRequest":
        return cls(
            recipe=Recipe.from_dict(data["recipe"]),
            source_ids=list(data.get("source_ids", [])),
            source_segment_ids=list(data.get("source_segment_ids", [])),
            source_paths=list(data.get("source_paths", [])),
            command=list(data.get("command", [])),
            guard_status=data["guard_status"],
            blocked_reasons=list(data.get("blocked_reasons", [])),
        )


@dataclass
class GenerationRequest:
    run_id: str
    created_at: str
    corpus_id: str
    source_map_path: str
    recipes_path: str | None = None
    notebook_id: str | None = None
    profile: str | None = None
    unsynced_segment_ids: list[str] = field(default_factory=list)
    synced_source_ids: list[str] = field(default_factory=list)
    recipe_requests: list[RecipeGenerationRequest] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "corpus_id": self.corpus_id,
            "source_map_path": self.source_map_path,
            "recipes_path": self.recipes_path,
            "notebook_id": self.notebook_id,
            "profile": self.profile,
            "unsynced_segment_ids": list(self.unsynced_segment_ids),
            "synced_source_ids": list(self.synced_source_ids),
            "recipe_requests": [request.to_dict() for request in self.recipe_requests],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationRequest":
        return cls(
            run_id=data["run_id"],
            created_at=data["created_at"],
            corpus_id=data["corpus_id"],
            source_map_path=data["source_map_path"],
            recipes_path=data.get("recipes_path"),
            notebook_id=data.get("notebook_id"),
            profile=data.get("profile"),
            unsynced_segment_ids=list(data.get("unsynced_segment_ids", [])),
            synced_source_ids=list(data.get("synced_source_ids", [])),
            recipe_requests=[
                RecipeGenerationRequest.from_dict(request)
                for request in data.get("recipe_requests", [])
            ],
        )


@dataclass
class RecipeGenerationResult:
    recipe_name: str
    artifact_kind: ArtifactKind
    command: list[str]
    status: GenerationExecutionStatus
    exit_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RecipeGenerationResult":
        return cls(
            recipe_name=data["recipe_name"],
            artifact_kind=data["artifact_kind"],
            command=list(data.get("command", [])),
            status=data["status"],
            exit_code=data.get("exit_code"),
            stdout=data.get("stdout"),
            stderr=data.get("stderr"),
        )


@dataclass
class GenerationRun:
    run_id: str
    executed_at: str
    request_path: str
    results: list[RecipeGenerationResult]

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "executed_at": self.executed_at,
            "request_path": self.request_path,
            "results": [result.to_dict() for result in self.results],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationRun":
        return cls(
            run_id=data["run_id"],
            executed_at=data["executed_at"],
            request_path=data["request_path"],
            results=[RecipeGenerationResult.from_dict(result) for result in data.get("results", [])],
        )


@dataclass
class GenerateStageResult:
    request: GenerationRequest
    run: GenerationRun | None = None

    def to_dict(self) -> dict:
        return {
            "request": self.request.to_dict(),
            "run": self.run.to_dict() if self.run is not None else None,
        }


@dataclass
class PublishedArtifact:
    recipe_name: str
    artifact_kind: ArtifactKind
    source_path: str | None
    output_path: str | None
    status: PublishStatus

    def to_dict(self) -> dict:
        return asdict(self)
