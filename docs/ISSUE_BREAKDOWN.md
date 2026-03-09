# Issue Breakdown

## Completed issues

### 1. Implement reading-map aware `pack`
Delivered:
- `pack` reads a concrete JSON reading map input
- output ordering follows the reading map deterministically
- unchanged notes keep the same `segment_id` because IDs derive from corpus-relative paths

### 2. Add explicit sync handoff and `source_map` updates
Delivered:
- `sync` ingests a partial manual update file with `segment_id` and `notebooklm_source_id`
- `source_map.json` persists status per segment and preserves unchanged synced entries
- `sync_handoff.json` makes the manual sync step explicit and file-backed

### 3. Wire recipe parameters into guarded generation
Delivered:
- `slides`, `audio`, and `report` recipes now carry language, source scope, and kind-specific parameters
- `generate` resolves effective `source_ids` against `source_map.json`
- `generation_request.json` records per-recipe guard status, selected sources, and concrete `nlm` create commands
- guarded execution can call `nlm slides create`, `nlm audio create`, and `nlm report create` and persist `generation_run.json`

### 4. Add stage and invocation-boundary tests
Delivered:
- tests run locally without live NotebookLM generation
- fixture-based coverage exercises `pack -> sync -> generate -> publish`
- guarded execution is covered with a fake runner at the CLI boundary
- stage failures point to explicit work-dir artifacts

### 5. Add roadmap-specific example bundle
Delivered:
- `examples/agent_first_engineering_roadmap/` provides a concise roadmap brief
- `source_index.json` makes scenario hierarchy explicit without checking raw article text into the repo
- repo-local `reading_map.json`, `recipes.json`, and sync template files anchor the current use case

### 6. Add run metadata and drift detection
Delivered:
- `source_drift.json` detects when the current `source_pack.json` no longer matches `source_map.json`
- `generate` surfaces drift before any guarded `nlm` execution and points recovery back to `sync`
- `run_metadata.json` summarizes the current pack, sync, drift, generate, and publish artifacts in one inspectable file

### 7. Tighten publish intake only if real downloads require it
Delivered:
- `publish` scans the downloads intake recursively for the expected stable filename per recipe
- repeated publish runs stay idempotent for unchanged inputs because output filenames remain recipe-based and stable
- `publish_manifest.json` records published, missing, or ambiguous intake clearly

### 8. Add a reading-map-first one-click entry
Delivered:
- `reading-map-run` gives the proven reading-map flow one narrow command instead of requiring stage-by-stage command choreography
- the command still writes the same explicit handoff files: `sync_handoff.json`, `generation_request.json`, and `publish_manifest.json` when downloads are present
- reruns can reuse `.work/manual_source_updates.json` and `.work/downloads/` without hiding the manual NotebookLM boundaries
- subprocess tests cover the new entry both before and after manual handoff files are present

## Remaining narrow issues

No additional narrow issues are queued beyond concrete corpus-driven bugs and failure-message polish.
