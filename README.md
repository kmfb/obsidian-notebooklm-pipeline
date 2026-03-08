# obsidian-notebooklm-pipeline

A narrow rewrite for turning an Obsidian-driven corpus into a NotebookLM production pipeline.

Phase 1 currently covers four explicit stages:
- `pack`: build a local Source Pack from an Obsidian corpus
- `sync`: record the explicit sync state between local segments and NotebookLM sources
- `generate`: assemble recipe-driven generation requests for slides, audio, and report outputs
- `publish`: pull downloaded artifacts back into stable local output folders

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
- `src/obsidian_notebooklm_pipeline/` — thin Python package
- `scripts/run_pipeline.py` — minimal CLI entry point for the scaffold
- `tests/fixtures/` — tiny corpus and file-backed stage fixtures

## Current behavior

Implemented now:
- `pack` can read a JSON reading map, select listed Markdown notes only, and preserve deterministic segment ordering
- `pack` writes stable `segment_id` values from corpus-relative note paths and persists per-segment text digests
- `sync` can ingest partial manual source-ID updates, preserve unchanged synced entries, and write both `source_map.json` and `sync_handoff.json`
- `generate` can load recipes from a documented JSON file or use defaults
- `publish` copies manually downloaded outputs into stable local folders and records the results in `publish_manifest.json`
- smoke tests cover `pack -> sync -> generate -> publish` without NotebookLM access

Still intentionally out of scope:
- NotebookLM upload automation
- NotebookLM generation automation
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
  --recipes /path/to/recipes.json

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
  --downloads-dir .work/downloads
```

## Working files

The pipeline writes predictable files under the chosen work directory:
- `source_pack.json`
- `source_map.json`
- `sync_handoff.json`
- `generation_request.json`
- `publish_manifest.json`
- `outputs/slides/`, `outputs/audio/`, `outputs/report/`

These files are the handoff surface between local prep, explicit NotebookLM actions, and future automation.

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
      "prompt_focus": "Teach the core ideas"
    },
    {
      "name": "lesson-audio",
      "artifact_kind": "audio",
      "prompt_focus": "Narrate the main ideas"
    },
    {
      "name": "lesson-report",
      "artifact_kind": "report",
      "prompt_focus": "Summarize the details"
    }
  ]
}
```

Supported `artifact_kind` values are `slides`, `audio`, and `report`.

## Tests

Run the current fixture-based smoke tests locally:

```bash
python3 -m unittest discover -s tests -v
```

## Next steps

The next intentionally narrow items are:
1. make `publish` naming and intake rules a bit stricter where it earns its keep
2. add drift detection between `source_pack.json` and `source_map.json`
3. keep improving failure messages without turning the repo into a framework
