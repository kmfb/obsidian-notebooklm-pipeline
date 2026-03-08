# Architecture

## Goal

Build a narrow, legible pipeline for:
1. packing an Obsidian corpus into a Source Pack
2. explicitly syncing segments into NotebookLM and persisting a `source_map`
3. generating slides, audio, and report requests from recipes and, when asked, calling guarded `nlm` create commands
4. publishing downloaded outputs back into local folders

This is a rewrite with a constrained first phase. The architecture is optimized for clarity, explicit state, and easy iteration rather than broad abstraction.

## Core model

### Corpus
A local Obsidian-backed collection of Markdown notes and supporting files.

### Segment
The smallest unit we care about for sync and generation. A segment is a locally identified chunk of source text with a stable `segment_id`, title, source path, full text body, and text digest.

### Source Pack
A local manifest of the corpus snapshot prepared for NotebookLM. It is file-backed, reproducible, and written to `source_pack.json`.

### Source Map
A persisted mapping between local `segment_id` values and NotebookLM source identifiers. It is the guardrail that keeps local and remote state aligned. It is written to `source_map.json`.

### Sync Handoff
A file-backed summary of the current sync state. It points at the current pack and source map, lists pending versus synced segments, and repeats the expected manual update file shape. It is written to `sync_handoff.json`.

### Recipe
A small declaration of what to generate. Recipes describe target outputs like `slides`, `audio`, or `report`, plus only the parameters that map directly to the current NotebookLM CLI surface. They are intentionally narrow and do not form a generic DAG or plugin system.

### Run
A single execution against a work directory. Runs are grounded in files, not in a background scheduler or workflow database.

## Narrow stage architecture

### 1. Pack
Input:
- corpus directory
- optional reading map path

Output:
- `source_pack.json`

Responsibility:
- discover source material
- assign stable local segment identifiers
- persist a source-pack snapshot for downstream stages

Implemented behavior:
- scans Markdown files deterministically when no reading map is provided
- reads an ordered JSON reading map when provided
- only packs listed Markdown files when using a reading map
- captures file path, title, full text, tags, and text digest
- keeps `segment_id` derived from the corpus-relative source path

### 2. Sync
Input:
- `source_pack.json`
- optional manual sync update file with `segment_id` and `notebooklm_source_id`

Output:
- `source_map.json`
- `sync_handoff.json`

Responsibility:
- make NotebookLM sync explicit
- persist source identity mapping durably
- surface unsynced segments clearly

Implemented behavior:
- does not automate NotebookLM upload
- accepts partial manual sync updates
- preserves unchanged synced entries across reruns
- records pending vs synced state per segment
- persists current segment metadata alongside NotebookLM source IDs

### 3. Generate
Input:
- `source_map.json`
- recipe set
- optional `notebook_id`
- optional NotebookLM profile name

Output:
- `generation_request.json`
- `generation_run.json` when guarded execution is requested

Responsibility:
- assemble recipe-driven generation intents
- resolve the effective `source_ids` for each recipe
- make guard status explicit before remote work starts
- call concrete `nlm` commands only when the run is ready and execution is requested

Implemented behavior:
- loads recipes from defaults or a local JSON file
- records per-recipe request details, source scope, and concrete `nlm` command in `generation_request.json`
- blocks full-corpus recipes when the source map still has pending segments
- blocks pinned recipes when requested `source_ids` are missing from the synced source map
- can execute `nlm slides create`, `nlm audio create`, and `nlm report create` directly through a guarded local boundary
- records blocked, created, and failed command results in `generation_run.json`

### 4. Publish
Input:
- downloaded output artifacts in a local intake folder
- `generation_request.json`

Output:
- copied files under `outputs/`
- `publish_manifest.json`

Responsibility:
- normalize local output layout
- copy artifacts into stable paths for later use
- record what was found versus missing

Implemented behavior:
- expects one file per recipe based on recipe name plus artifact extension
- copies matching local files if present
- records missing files without crashing
- does not automate remote download

## Data flow

```text
corpus/notes + reading_map.json -> pack -> source_pack.json
source_pack.json + manual sync updates -> sync -> source_map.json + sync_handoff.json
source_map.json + recipes.json -> generate -> generation_request.json -> guarded nlm create -> generation_run.json
manual downloads + generation_request.json -> publish -> outputs/ + publish_manifest.json
```

Each stage reads a small number of explicit inputs and writes stable artifacts. This keeps the repo easy to inspect and friendly to agentic iteration.

## Mechanical guardrails

- Stable work-dir filenames instead of hidden state
- Typed datamodels close to the stage logic
- Thin IO helpers instead of framework-heavy infrastructure
- Explicit `pending` and `blocked` states instead of pretending remote work succeeded
- Script entry point that mirrors the four stages directly
- Fixture-based smoke tests around stage boundaries and guarded CLI invocation

## Parse, don't validate

The pipeline favors simple typed parsing of repo-owned files over deep validation layers. When external data enters the system, keep parsing logic near the boundary and let failures be direct and obvious.

## Non-goals

These remain out of scope for the current phase:
- a generic workflow engine
- background job orchestration
- backward compatibility with any prior repo shape
- `book` and `chapter` as top-level concepts
- vendor-neutral source sync abstractions
- hidden NotebookLM automation that obscures which command really ran
- large schema or plugin frameworks before the core flow is proven

## Repo legibility standard

A new contributor should be able to answer these quickly by reading the repo:
- What are the four supported stages?
- Which file does each stage read and write?
- Where is local-vs-NotebookLM identity stored?
- Which parts are implemented versus intentionally stubbed?

If a change makes those answers harder to find, it is probably overdesigned for this phase.
