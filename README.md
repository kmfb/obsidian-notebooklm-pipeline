# obsidian-notebooklm-pipeline

A narrow rewrite for turning an Obsidian-driven corpus into a NotebookLM production pipeline.

Phase 1 currently covers four explicit stages:
- `pack`: build a local Source Pack from an Obsidian corpus
- `sync`: record the explicit sync state between local segments and NotebookLM sources
- `generate`: assemble recipe-driven generation requests and, when asked, run guarded `nlm` create commands for slides, audio, and report outputs
- `publish`: pull downloaded outputs back into stable local output folders

This repo is intentionally small. It does **not** try to be a generic workflow engine, job runner, or vendor-neutral orchestration layer.

## Design constraints

- Prefer `corpus`, `segment`, `recipe`, and `run` over `book` or `chapter`
- Keep stage boundaries explicit and file-backed
- Treat plans and manifests as first-class repo artifacts
- Prefer parse-don't-validate data flows over sprawling schema frameworks
- Add mechanical guardrails with a clear directory layout and stable file names
- Stay honest about NotebookLM integration; no fake automation in the scaffold

## Repo layout

- `docs/ARCHITECTURE.md` — narrow system design and non-goals
- `docs/PLANS.md` — phased execution plan and current status
- `docs/ISSUE_BREAKDOWN.md` — issue status for the narrow first wave
- `examples/agent_first_engineering_roadmap/` — thin roadmap bundle for the current reading-map use case
- `src/obsidian_notebooklm_pipeline/` — thin Python package
- `scripts/run_pipeline.py` — minimal CLI entry point for the scaffold
- `tests/fixtures/` — tiny corpus and file-backed stage fixtures

## Current behavior

Implemented now:
- `pack` can read a JSON reading map, select listed Markdown notes only, and preserve deterministic segment ordering
- `pack` writes stable `segment_id` values from corpus-relative note paths and persists per-segment text digests
- `sync` can ingest partial manual source-ID updates, preserve unchanged synced entries, and write both `source_map.json` and `sync_handoff.json`
- `generate` can load recipes from a documented JSON file or use defaults
- `generate` resolves effective `source_ids`, carries recipe parameters into concrete `nlm` commands, and writes the inspectable result to `generation_request.json`
- `generate --execute` runs guarded `nlm <artifact> create ...` commands and records results in `generation_run.json`
- `publish` copies manually downloaded outputs into stable local folders and records the results in `publish_manifest.json`
- fixture tests cover request assembly, guarded execution boundaries, and `pack -> sync -> generate -> publish` without live NotebookLM generation

Still intentionally out of scope:
- NotebookLM upload automation
- NotebookLM download automation
- generic workflow or plugin abstractions

## Quickstart

1. Create a virtual environment if you want one.
2. Run the stages directly:

```bash
python3 scripts/run_pipeline.py pack \
  --corpus-dir /path/to/corpus \
  --work-dir .work \
  --reading-map /path/to/reading_map.json

python3 scripts/run_pipeline.py sync \
  --work-dir .work \
  --source-ids .work/manual_source_updates.json

python3 scripts/run_pipeline.py generate \
  --work-dir .work \
  --recipes /path/to/recipes.json \
  --notebook-id your-notebook-id

python3 scripts/run_pipeline.py generate \
  --work-dir .work \
  --recipes /path/to/recipes.json \
  --notebook-id your-notebook-id \
  --execute

python3 scripts/run_pipeline.py publish \
  --work-dir .work \
  --downloads-dir .work/downloads
```

Or run the narrow end-to-end skeleton:

```bash
python3 scripts/run_pipeline.py all \
  --corpus-dir /path/to/corpus \
  --work-dir .work \
  --reading-map /path/to/reading_map.json \
  --source-ids .work/manual_source_updates.json \
  --recipes /path/to/recipes.json \
  --notebook-id your-notebook-id \
  --downloads-dir .work/downloads
```

Add `--execute-generate` to `all` only when you want the run to call `nlm` directly.

## Working files

The pipeline writes predictable files under the chosen work directory:
- `source_pack.json`
- `source_map.json`
- `sync_handoff.json`
- `generation_request.json`
- `generation_run.json` when guarded execution is requested
- `publish_manifest.json`
- `outputs/slides/`, `outputs/audio/`, `outputs/report/`

These files are the handoff surface between local prep, explicit NotebookLM actions, and local publish intake.

## Reading map format

`pack` accepts a JSON reading map with an ordered `segments` list:

```json
{
  "segments": [
    {
      "source_path": "notes/foundations.md",
      "tags": ["core", "week-1"]
    },
    {
      "source_path": "notes/applications.md",
      "tags": ["core", "week-2"]
    }
  ]
}
```

Rules:
- `source_path` is required and must point to a Markdown file under the corpus directory
- list order becomes segment order in `source_pack.json`
- only listed notes are packed when a reading map is provided
- `segment_id` stays derived from the corpus-relative path, so unchanged notes keep the same ID across repacks

## Sync update format

`sync` accepts a JSON file with partial manual source-ID updates:

```json
{
  "updates": [
    {
      "segment_id": "notes--foundations",
      "notebooklm_source_id": "source-foundations"
    },
    {
      "segment_id": "notes--applications",
      "notebooklm_source_id": "source-applications"
    }
  ]
}
```

Rules:
- omitted segments keep their existing `source_map.json` state
- `null` can be used to clear a prior mapping for a segment
- `sync_handoff.json` summarizes pending vs synced segments and repeats the expected update shape

## Recipe format

`generate` accepts a JSON recipe file with a top-level `recipes` list:

```json
{
  "recipes": [
    {
      "name": "lesson-slides",
      "artifact_kind": "slides",
      "language": "en",
      "focus": "Teach the core ideas",
      "format": "detailed_deck",
      "length": "default"
    },
    {
      "name": "lesson-audio",
      "artifact_kind": "audio",
      "language": "en",
      "focus": "Narrate the main ideas",
      "source_ids": ["source-foundations", "source-applications"],
      "format": "deep_dive",
      "length": "long"
    },
    {
      "name": "lesson-report",
      "artifact_kind": "report",
      "language": "en",
      "source_ids": ["source-foundations"],
      "format": "Create Your Own",
      "prompt": "Write a concise study report with next actions."
    }
  ]
}
```

Supported values:
- `artifact_kind`: `slides`, `audio`, `report`
- `slides` format: `detailed_deck`, `presenter_slides`
- `slides` length: `short`, `default`
- `audio` format: `deep_dive`, `brief`, `critique`, `debate`
- `audio` length: `short`, `default`, `long`
- `report` format: `Briefing Doc`, `Study Guide`, `Blog Post`, `Create Your Own`
- `prompt` is only valid for `report` with `format: "Create Your Own"`

Guardrails:
- when a recipe omits `source_ids`, `generate` only marks it ready if the whole `source_map.json` is synced
- when a recipe sets `source_ids`, those IDs must already exist in `source_map.json`
- `generation_request.json` records the effective `source_ids`, selected segments, and concrete `nlm` command for each recipe

## Roadmap bundle

The current roadmap-specific example bundle lives in `examples/agent_first_engineering_roadmap/` and includes:
- `roadmap_brief.md` — concise scenario brief
- `source_index.json` — explicit hierarchy for the roadmap corpus slice
- `reading_map.json` — ordered segment list for `pack`
- `recipes.json` — scenario-specific generation recipes
- `manual_source_updates.example.json` — thin sync template

The bundle is intentionally path-driven. It does not check raw article text into the repo.

## Tests

Run the current fixture-based tests locally:

```bash
python3 -m unittest discover -s tests -v
```

## Next steps

The next intentionally narrow items are:
1. surface drift between `source_pack.json` and `source_map.json` before generation
2. tighten publish intake rules only if real download patterns force it
3. keep improving failure messages without turning the repo into a framework
