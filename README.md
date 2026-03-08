# obsidian-notebooklm-pipeline

A narrow rewrite for turning an Obsidian-driven corpus into a NotebookLM production pipeline.

Phase 1 only covers four explicit stages:
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
- `docs/PLANS.md` — phased execution plan
- `docs/ISSUE_BREAKDOWN.md` — proposed initial GitHub issues
- `src/obsidian_notebooklm_pipeline/` — thin Python package
- `scripts/run_pipeline.py` — minimal CLI entry point for the scaffold

## Current scaffold behavior

The code is intentionally thin but runnable:
- `pack` scans Markdown files in a corpus directory and writes `source_pack.json`
- `sync` writes `source_map.json` from an optional manual source-id mapping file
- `generate` writes `generation_request.json` from recipes and the current source map
- `publish` copies any manually downloaded artifacts into stable output folders and writes `publish_manifest.json`

NotebookLM upload, generation, and download automation are **not** implemented yet.

## Quickstart

1. Create a virtual environment if you want one.
2. Run a stage directly:

```bash
python3 scripts/run_pipeline.py pack --corpus-dir /path/to/obsidian/vault --work-dir .work
python3 scripts/run_pipeline.py sync --work-dir .work --source-ids .work/manual_source_ids.json
python3 scripts/run_pipeline.py generate --work-dir .work
python3 scripts/run_pipeline.py publish --work-dir .work --downloads-dir .work/downloads
```

Or run the narrow end-to-end skeleton:

```bash
python3 scripts/run_pipeline.py all --corpus-dir /path/to/obsidian/vault --work-dir .work
```

## Working files

The scaffold writes predictable files under the chosen work directory:
- `source_pack.json`
- `source_map.json`
- `generation_request.json`
- `publish_manifest.json`
- `outputs/slides/`, `outputs/audio/`, `outputs/report/`

These files are the handoff surface between local prep, explicit NotebookLM actions, and future automation.

## Next steps

Start with the issues in `docs/ISSUE_BREAKDOWN.md`. The first useful implementation work is:
1. real Obsidian reading-map aware packing
2. explicit NotebookLM sync handoff tooling
3. recipe loading and generation request shaping
4. local publish intake and smoke tests
