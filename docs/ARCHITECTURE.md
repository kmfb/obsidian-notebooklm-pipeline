# Architecture

## Goal

Build a narrow, legible pipeline for:
1. packing an Obsidian corpus into a Source Pack
2. explicitly syncing segments into NotebookLM and persisting a `source_map`
3. generating slides, audio, and report requests from recipes
4. publishing downloaded outputs back into local folders

This is a rewrite with a constrained first phase. The architecture is optimized for clarity, explicit state, and easy iteration rather than broad abstraction.

## Core model

### Corpus
A local Obsidian-backed collection of Markdown notes and supporting files. In phase 1, the scaffold treats the corpus as a directory of Markdown files.

### Segment
The smallest unit we care about for sync and generation. A segment is a locally identified chunk of source text with a stable `segment_id`, title, source path, and text body.

### Source Pack
A local manifest of the corpus snapshot prepared for NotebookLM. It is file-backed and reproducible. In phase 1 it is written to `source_pack.json`.

### Source Map
A persisted mapping between local `segment_id` values and NotebookLM source identifiers. This is the key guardrail that keeps local and remote state aligned. In phase 1 it is written to `source_map.json`.

### Recipe
A small declaration of what to generate. Recipes describe target outputs like `slides`, `audio`, or `report`. They are intentionally narrow and do not form a generic DAG or plugin system.

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

Phase 1 scaffold behavior:
- scans Markdown files
- captures file path, title, and full text
- does not yet implement reading-map aware ordering or chunking

### 2. Sync
Input:
- `source_pack.json`
- optional manual mapping file of `segment_id -> notebooklm_source_id`

Output:
- `source_map.json`

Responsibility:
- make NotebookLM sync explicit
- persist source identity mapping
- surface unsynced segments clearly

Phase 1 scaffold behavior:
- does not automate NotebookLM upload
- records sync state from manual handoff data
- marks missing mappings as `pending`

### 3. Generate
Input:
- `source_map.json`
- recipe set

Output:
- `generation_request.json`

Responsibility:
- assemble recipe-driven generation intents
- keep requested artifacts explicit and file-backed
- make unsynced preconditions visible before downstream work

Phase 1 scaffold behavior:
- emits a generation request manifest only
- does not call NotebookLM generation APIs or browser automation

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

Phase 1 scaffold behavior:
- copies matching local files if present
- does not automate remote download

## Data flow

```text
corpus/notes -> pack -> source_pack.json
source_pack.json + explicit sync handoff -> sync -> source_map.json
source_map.json + recipes -> generate -> generation_request.json
manual downloads + generation_request.json -> publish -> outputs/ + publish_manifest.json
```

Each stage reads a small number of explicit inputs and writes one stable artifact. This keeps the repo easy to inspect and friendly to agentic iteration.

## Mechanical guardrails

- Stable work-dir filenames instead of hidden state
- Typed datamodels close to the stage logic
- Thin IO helpers instead of framework-heavy infrastructure
- Explicit `pending` states instead of pretending remote work succeeded
- Script entry point that mirrors the four stages directly

## Parse, don't validate

The scaffold favors simple typed parsing of repo-owned files over deep validation layers. The working assumption is that downstream stages consume manifests produced by prior local stages. When external data enters the system, keep parsing logic near the boundary and let failures be direct and obvious.

## Non-goals

These are out of scope for the first phase:
- a generic workflow engine
- background job orchestration
- backward compatibility with any prior repo shape
- `book` and `chapter` as top-level concepts
- vendor-neutral source sync abstractions
- fake NotebookLM automation or mock integrations that imply completeness
- large schema or plugin frameworks before the core flow is proven

## Repo legibility standard

A new contributor should be able to answer these quickly by reading the repo:
- What are the four supported stages?
- Which file does each stage read and write?
- Where is local-vs-NotebookLM identity stored?
- Which parts are implemented versus intentionally stubbed?

If a change makes those answers harder to find, it is probably overdesigned for this phase.
