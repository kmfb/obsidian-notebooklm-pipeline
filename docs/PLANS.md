# Plans

## Current status

Implemented in the repo now:
- reading-map aware `pack`
- durable `source_map.json` updates with explicit `sync_handoff.json`
- file-backed `source_drift.json` detection against the current source pack
- documented JSON recipes for `slides`, `audio`, and `report`
- guarded generation request assembly that carries recipe parameters into concrete `nlm` create commands and blocks drifted runs
- optional guarded execution that records `generation_run.json`
- recursive publish intake with missing versus ambiguous artifact reporting
- `run_metadata.json` summaries for the current work-dir artifacts
- roadmap-specific example manifests for the agent-first engineering roadmap use case
- fixture-based tests for `pack -> sync -> generate -> publish` plus guarded execution boundaries

Still intentionally narrow:
- no NotebookLM upload automation
- no NotebookLM download automation
- no generic workflow abstractions

## Phase 1: Make `pack` genuinely useful

Delivered:
- reads an explicit reading map file
- selects source notes from that map
- preserves deterministic segment ordering
- keeps `segment_id` stable from corpus-relative note paths

Remaining narrow follow-up:
- improve segment identity only if a real corpus case proves path-based IDs insufficient

## Phase 2: Make `sync` explicit and dependable

Delivered:
- supports a deliberate human-or-agent sync workflow
- persists `source_map.json` cleanly across reruns
- accepts partial manual source-ID updates
- writes `sync_handoff.json` as the explicit local handoff artifact

Remaining narrow follow-up:
- keep drift reporting limited to current local artifacts

## Phase 3: Make `generate` recipe-driven and inspectable

Delivered:
- defines a small JSON recipe format for `slides`, `audio`, and `report`
- resolves effective `source_ids` per recipe from the current `source_map.json`
- writes `generation_request.json` with per-recipe guard status, drift metadata, and concrete `nlm` commands
- can execute guarded `nlm` create commands and persist `generation_run.json`

Remaining narrow follow-up:
- keep generation guardrails narrow and file-backed

## Phase 4: Make `publish` operational

Delivered:
- standardizes local output folders by artifact kind
- copies downloaded artifacts into stable output paths
- writes `publish_manifest.json` with published, missing, or ambiguous intake status
- accepts recursive local intake while keeping output filenames stable

Remaining narrow follow-up:
- tighten naming rules only if real downloaded files require it

## Phase 5: Add guardrails, not framework

Delivered:
- added focused tests around the stage boundaries
- added guarded execution tests around the `nlm` invocation boundary
- added drift detection tests and clean publish intake tests
- added a roadmap bundle for the current reading-map scenario
- kept test coverage at implemented behavior only

Remaining narrow follow-up:
- add small failure-mode tests as real bugs appear
