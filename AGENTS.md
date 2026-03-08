# AGENTS.md

This repo is a **narrow pipeline**, not a platform.

## What this repo is for

Turn an Obsidian-driven corpus into a file-backed NotebookLM workflow:

1. `pack` → build `source_pack.json`
2. `sync` → persist `source_map.json`
3. `generate` → emit `generation_request.json`
4. `publish` → normalize downloaded outputs into stable local folders

Phase 1 only targets:
- Obsidian corpus / reading map input
- NotebookLM source sync handoff
- recipe-driven `slides` / `audio` / `report`
- local publish intake

## What this repo is NOT

Do **not** turn this into:
- a generic workflow engine
- a background job runner
- a plugin framework
- a vendor-neutral abstraction layer
- a backward-compatibility museum
- fake NotebookLM automation that pretends more is implemented than actually exists

If a change makes the repo feel “flexible” but harder to read, it is probably the wrong change.

## Top-level language

Prefer these terms everywhere:
- `corpus`
- `segment`
- `recipe`
- `run`

Avoid using `book` / `chapter` as the top-level system model.
If those terms appear, they should stay at the edge for specific inputs, not define the whole architecture.

## Read these first

Before editing code, read:
1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/PLANS.md`
4. `docs/ISSUE_BREAKDOWN.md`

These files are the repo map. Keep them updated when behavior changes.

## Implementation rules

- Keep stage boundaries explicit and file-backed.
- Each stage should have obvious inputs and outputs.
- Prefer small datamodels near the stage logic.
- Prefer parse-at-the-boundary over sprawling validation layers.
- Be honest about stubs, TODOs, and manual handoff steps.
- Add tests for real implemented behavior only.
- Keep the happy path legible from the CLI and fixture tests.

## Expected stage artifacts

Under a chosen work dir, the main artifacts are:
- `source_pack.json`
- `source_map.json`
- `generation_request.json`
- `publish_manifest.json`
- `outputs/slides/`
- `outputs/audio/`
- `outputs/report/`

Do not hide critical state in logs or implicit runtime memory when a stable file should exist.

## Commands

Run stages directly:

```bash
python3 scripts/run_pipeline.py pack --corpus-dir /path/to/corpus --work-dir .work
python3 scripts/run_pipeline.py sync --work-dir .work --source-ids .work/manual_source_ids.json
python3 scripts/run_pipeline.py generate --work-dir .work
python3 scripts/run_pipeline.py publish --work-dir .work --downloads-dir .work/downloads
```

Run the current end-to-end skeleton:

```bash
python3 scripts/run_pipeline.py all --corpus-dir /path/to/corpus --work-dir .work
```

## When making changes

Prefer changes that make these questions easy to answer:
- What stage am I in?
- What file does this stage read?
- What file does this stage write?
- Where is local-vs-NotebookLM identity stored?
- Which part is real, and which part is still a stub?

If you cannot answer those quickly after your change, simplify it.
