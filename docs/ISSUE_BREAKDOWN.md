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

### 3. Define the recipe file format
Delivered:
- `slides`, `audio`, and `report` recipes are supported
- `generate` loads recipes from disk via a documented JSON file format
- `generation_request.json` reflects recipe metadata directly

### 4. Add stage smoke tests with a fixture corpus
Delivered:
- tests run locally without NotebookLM access
- fixture-based smoke coverage exercises `pack -> sync -> generate -> publish`
- stage failures point to explicit work-dir artifacts

## Remaining narrow issues

### 5. Make `publish` handle downloaded artifact intake cleanly
Goal:
- turn publish into a predictable local file movement step

Next narrow scope:
- refine expected filenames only if real download patterns force it
- keep repeated publish runs idempotent for unchanged inputs
- record found versus missing artifacts clearly

### 6. Add run metadata and drift detection
Goal:
- make it easier to reason about what a given set of artifacts came from

Next narrow scope:
- detect when `source_map.json` no longer matches the current `source_pack.json`
- surface drift before generation
- explain recovery steps in docs without widening the architecture
