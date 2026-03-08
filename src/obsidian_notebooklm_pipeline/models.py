from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

ArtifactKind = Literal["slides", "audio", "report"]
SyncStatus = Literal["pending", "synced"]
PublishStatus = Literal["missing", "published"]


@dataclass(frozen=True)
class Segment:
    segment_id: str
    title: str
    source_path: str
    text: str
    order: int
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourcePack:
    corpus_id: str
    generated_at: str
    segments: list[Segment]

    def to_dict(self) -> dict:
        return {
            "corpus_id": self.corpus_id,
            "generated_at": self.generated_at,
            "segments": [segment.to_dict() for segment in self.segments],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SourcePack":
        return cls(
            corpus_id=data["corpus_id"],
            generated_at=data["generated_at"],
            segments=[Segment(**segment) for segment in data["segments"]],
        )


@dataclass
class SourceMapEntry:
    segment_id: str
    notebooklm_source_id: str | None
    sync_status: SyncStatus

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
    unsynced_segment_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "corpus_id": self.corpus_id,
            "recipes": [recipe.to_dict() for recipe in self.recipes],
            "source_map_path": self.source_map_path,
            "unsynced_segment_ids": list(self.unsynced_segment_ids),
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
