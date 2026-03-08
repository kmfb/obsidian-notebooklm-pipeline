# Issue Breakdown

## Best first issues

### 1. Implement reading-map aware `pack`
Goal:
- make the pack stage reflect the intended Obsidian-driven corpus shape instead of scanning every Markdown file

Scope:
- define reading-map input expectations
- select and order source files from that map
- keep segment IDs stable across repeated pack runs

Acceptance criteria:
- `pack` reads a concrete reading-map input
- output ordering is deterministic
- unchanged notes keep the same `segment_id`

### 2. Add explicit sync handoff and `source_map` updates
Goal:
- turn sync from a placeholder mapping import into a deliberate human-or-agent handoff step

Scope:
- define the manual mapping file format
- support partial sync updates
- surface pending and synced entries clearly

Acceptance criteria:
- `sync` can ingest a mapping file with partial source IDs
- `source_map.json` persists status per segment
- unchanged synced entries survive reruns cleanly

### 3. Define the recipe file format
Goal:
- make slides/audio/report generation requests declarative and editable

Scope:
- define the recipe schema shape for phase 1
- support a local JSON recipe file in addition to defaults
- document recipe examples in the README or docs

Acceptance criteria:
- at least three recipe kinds are supported: `slides`, `audio`, `report`
- `generate` can load recipes from disk
- generation manifest reflects recipe metadata directly

### 4. Add stage smoke tests with a fixture corpus
Goal:
- lock in the minimal flow without introducing framework complexity

Scope:
- create a tiny fixture corpus
- test `pack`, `sync`, `generate`, and `publish` in sequence
- verify output files exist and contain the expected top-level fields

Acceptance criteria:
- tests run locally without NotebookLM access
- stage outputs are reproducible for the fixture input
- failures point to a specific stage artifact

### 5. Make `publish` handle downloaded artifact intake cleanly
Goal:
- turn publish into a predictable local file movement step

Scope:
- define expected filenames or a small naming convention
- copy artifacts into `outputs/slides`, `outputs/audio`, and `outputs/report`
- record found versus missing artifacts in the publish manifest

Acceptance criteria:
- publish copies matching local files into stable folders
- missing files are recorded without crashing the run
- repeated publish runs are idempotent for unchanged inputs

### 6. Add run metadata and drift detection
Goal:
- make it easier to reason about what a given set of artifacts came from

Scope:
- record run IDs and timestamps consistently
- detect when `source_map.json` no longer matches the current `source_pack.json`
- expose drift in `generate` preconditions

Acceptance criteria:
- generated manifests include a run identifier
- drifted segments are surfaced before generation
- docs explain how to recover from drift

## Nice-to-have after the first wave

- add a tiny example corpus under `examples/`
- add structured logging for stage summaries
- add a minimal `Makefile` or task runner only if it reduces repetition
