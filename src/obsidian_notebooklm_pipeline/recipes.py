from __future__ import annotations

from pathlib import Path

from .io import read_json
from .models import Recipe

SLIDES_FORMATS = {"detailed_deck", "presenter_slides"}
SLIDES_LENGTHS = {"short", "default"}
AUDIO_FORMATS = {"deep_dive", "brief", "critique", "debate"}
AUDIO_LENGTHS = {"short", "default", "long"}
REPORT_FORMATS = {"Briefing Doc", "Study Guide", "Blog Post", "Create Your Own"}

DEFAULT_RECIPES: list[Recipe] = [
    Recipe(
        name="slides-default",
        artifact_kind="slides",
        language="en",
        focus="Teaching-oriented slide deck",
        format="detailed_deck",
        length="default",
    ),
    Recipe(
        name="audio-default",
        artifact_kind="audio",
        language="en",
        focus="Narrated audio overview",
        format="deep_dive",
        length="default",
    ),
    Recipe(
        name="report-default",
        artifact_kind="report",
        language="en",
        format="Briefing Doc",
    ),
]

ARTIFACT_EXTENSIONS = {
    "slides": ".pdf",
    "audio": ".m4a",
    "report": ".md",
}

ALLOWED_ARTIFACT_KINDS = set(ARTIFACT_EXTENSIONS)


def _validate_text_list(values: tuple[str, ...], field_name: str, recipe_name: str) -> None:
    if not all(isinstance(value, str) and value for value in values):
        raise ValueError(f"Recipe '{recipe_name}' field '{field_name}' must contain non-empty strings")


def _validate_recipe(recipe: Recipe) -> None:
    if recipe.artifact_kind not in ALLOWED_ARTIFACT_KINDS:
        raise ValueError(f"Unsupported artifact_kind: {recipe.artifact_kind}")
    if recipe.language is not None and not recipe.language:
        raise ValueError(f"Recipe '{recipe.name}' has an empty language")
    if recipe.focus is not None and not recipe.focus:
        raise ValueError(f"Recipe '{recipe.name}' has an empty focus")
    if recipe.prompt is not None and not recipe.prompt:
        raise ValueError(f"Recipe '{recipe.name}' has an empty prompt")

    _validate_text_list(recipe.source_ids, "source_ids", recipe.name)

    if recipe.artifact_kind == "slides":
        if recipe.format is not None and recipe.format not in SLIDES_FORMATS:
            raise ValueError(f"Recipe '{recipe.name}' has unsupported slides format: {recipe.format}")
        if recipe.length is not None and recipe.length not in SLIDES_LENGTHS:
            raise ValueError(f"Recipe '{recipe.name}' has unsupported slides length: {recipe.length}")
        if recipe.prompt is not None:
            raise ValueError(f"Recipe '{recipe.name}' cannot set prompt for slides")

    elif recipe.artifact_kind == "audio":
        if recipe.format is not None and recipe.format not in AUDIO_FORMATS:
            raise ValueError(f"Recipe '{recipe.name}' has unsupported audio format: {recipe.format}")
        if recipe.length is not None and recipe.length not in AUDIO_LENGTHS:
            raise ValueError(f"Recipe '{recipe.name}' has unsupported audio length: {recipe.length}")
        if recipe.prompt is not None:
            raise ValueError(f"Recipe '{recipe.name}' cannot set prompt for audio")

    elif recipe.artifact_kind == "report":
        if recipe.focus is not None:
            raise ValueError(f"Recipe '{recipe.name}' cannot set focus for report")
        if recipe.length is not None:
            raise ValueError(f"Recipe '{recipe.name}' cannot set length for report")
        if recipe.format is not None and recipe.format not in REPORT_FORMATS:
            raise ValueError(f"Recipe '{recipe.name}' has unsupported report format: {recipe.format}")
        if recipe.format == "Create Your Own" and not recipe.prompt:
            raise ValueError(f"Recipe '{recipe.name}' must set prompt for report format 'Create Your Own'")
        if recipe.prompt is not None and recipe.format != "Create Your Own":
            raise ValueError(
                f"Recipe '{recipe.name}' can only set prompt when report format is 'Create Your Own'"
            )


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
        if recipe.name in seen_names:
            raise ValueError(f"Duplicate recipe name: {recipe.name}")
        _validate_recipe(recipe)
        seen_names.add(recipe.name)
        recipes.append(recipe)

    return recipes


def expected_artifact_name(recipe: Recipe) -> str:
    return f"{recipe.name}{ARTIFACT_EXTENSIONS[recipe.artifact_kind]}"
