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

ALLOWED_ARTIFACT_KINDS = set(ARTIFACT_EXTENSIONS)


def load_recipes(recipes_path: Path | None = None) -> list[Recipe]:
    if recipes_path is None:
        return list(DEFAULT_RECIPES)

    payload = read_json(recipes_path)
    recipe_items = payload.get("recipes")
    if not isinstance(recipe_items, list) or not recipe_items:
        raise ValueError("Recipe file must contain a non-empty 'recipes' list")

    recipes: list[Recipe] = []
    seen_names: set[str] = set()
    for item in recipe_items:
        recipe = Recipe.from_dict(item)
        if recipe.artifact_kind not in ALLOWED_ARTIFACT_KINDS:
            raise ValueError(f"Unsupported artifact_kind: {recipe.artifact_kind}")
        if recipe.name in seen_names:
            raise ValueError(f"Duplicate recipe name: {recipe.name}")
        seen_names.add(recipe.name)
        recipes.append(recipe)

    return recipes


def expected_artifact_name(recipe: Recipe) -> str:
    return f"{recipe.name}{ARTIFACT_EXTENSIONS[recipe.artifact_kind]}"
