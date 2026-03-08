from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

ArtifactKind = Literal["slides", "audio", "report"]
PackSelectionMode = Literal["scan", "reading_map"]
SyncStatus = Literal["pending", "synced"]
PublishStatus = Literal["missing", "published"]


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
    prompt_focus: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Recipe":
        return cls(
            name=data["name"],
            artifact_kind=data["artifact_kind"],
            prompt_focus=data.get("prompt_focus", ""),
        )


@dataclass
class GenerationRequest:
    run_id: str
    created_at: str
    corpus_id: str
    recipes: list[Recipe]
    source_map_path: str
    recipes_path: str | None = None
    unsynced_segment_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "corpus_id": self.corpus_id,
            "recipes": [recipe.to_dict() for recipe in self.recipes],
            "source_map_path": self.source_map_path,
            "recipes_path": self.recipes_path,
            "unsynced_segment_ids": list(self.unsynced_segment_ids),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationRequest":
        return cls(
            run_id=data["run_id"],
            created_at=data["created_at"],
            corpus_id=data["corpus_id"],
            recipes=[Recipe.from_dict(recipe) for recipe in data["recipes"]],
            source_map_path=data["source_map_path"],
            recipes_path=data.get("recipes_path"),
            unsynced_segment_ids=list(data.get("unsynced_segment_ids", [])),
        )


@dataclass
class PublishedArtifact:
    recipe_name: str
    artifact_kind: ArtifactKind
    source_path: str | None
    output_path: str | None
    status: PublishStatus

    def to_dict(self) -> dict:
        return asdict(self)
