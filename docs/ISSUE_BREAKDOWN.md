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

## Remaining narrow issues

### 6. Add run metadata and drift detection
Goal:
- make it easier to reason about what a given set of artifacts came from

Next narrow scope:
- detect when `source_map.json` no longer matches the current `source_pack.json`
- surface drift before generation
- explain recovery steps in docs without widening the architecture

### 7. Tighten publish intake only if real downloads require it
Goal:
- turn publish into a predictable local file movement step

Next narrow scope:
- refine expected filenames only if real download patterns force it
- keep repeated publish runs idempotent for unchanged inputs
- record found versus missing artifacts clearly
