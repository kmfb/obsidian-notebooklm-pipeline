# Plans

## Current status

Implemented in the repo now:
- reading-map aware `pack`
- durable `source_map.json` updates with explicit `sync_handoff.json`
- documented JSON recipes for `slides`, `audio`, and `report`
- fixture-based smoke tests for `pack -> sync -> generate -> publish`

Still intentionally narrow:
- no NotebookLM upload automation
- no NotebookLM generation automation
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
- surface drift between current segment digests and synced state

## Phase 3: Make `generate` recipe-driven

Delivered:
- defines a small JSON recipe format for `slides`, `audio`, and `report`
- loads recipes from disk or defaults
- writes `generation_request.json` with recipe metadata and sync preconditions

Remaining narrow follow-up:
- decide whether recipe-level output naming needs one more field beyond `name`

## Phase 4: Make `publish` operational

Delivered:
- standardizes local output folders by artifact kind
- copies downloaded artifacts into stable output paths
- writes `publish_manifest.json` with published vs missing status

Remaining narrow follow-up:
- tighten naming rules only if real downloaded files require it

## Phase 5: Add guardrails, not framework

Delivered:
- added focused tests around the stage boundaries
- added a fixture corpus for pack/sync/generate/publish flows
- kept test coverage at implemented behavior only

Remaining narrow follow-up:
- add small failure-mode tests as real bugs appear
