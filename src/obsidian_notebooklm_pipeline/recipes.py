from __future__ import annotations

from pathlib import Path

from .io import read_json
from .models import Recipe

DEFAULT_RECIPES: list[Recipe] = [
    Recipe(name="slides-default", artifact_kind="slides", prompt_focus="Teaching-oriented slide deck"),
    Recipe(name="audio-default", artifact_kind="audio", prompt_focus="Narrated audio overview"),
    Recipe(name="report-default", artifact_kind="report", prompt_focus="Written summary report"),
]

ARTIFACT_EXTENSIONS = {
    "slides": ".pdf",
    "audio": ".mp3",
    "report": ".md",
}


def load_recipes(recipes_path: Path | None = None) -> list[Recipe]:
    if recipes_path is None:
        return list(DEFAULT_RECIPES)

    payload = read_json(recipes_path)
    return [Recipe.from_dict(item) for item in payload]


def expected_artifact_name(recipe: Recipe) -> str:
    return f"{recipe.name}{ARTIFACT_EXTENSIONS[recipe.artifact_kind]}"
