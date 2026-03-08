# Plans

## Phase 0: Scaffold the narrow rewrite

Deliverables:
- real README
- architecture document with explicit non-goals
- phased plan and issue breakdown
- thin Python package and script skeleton
- local work-dir conventions for stage artifacts

Exit criteria:
- repo explains itself without oral history
- a contributor can run each stage skeleton locally

## Phase 1: Make `pack` genuinely useful

Goals:
- read Obsidian corpus inputs deliberately
- incorporate reading-map driven segment selection and ordering
- improve segment identity stability across repacks

Suggested outputs:
- `source_pack.json` stays the single downstream handoff artifact
- tests for Markdown discovery, title extraction, and segment ID stability

Exit criteria:
- pack output is deterministic for the same corpus snapshot
- reading-map semantics are reflected in the pack manifest

## Phase 2: Make `sync` explicit and dependable

Goals:
- support a human-in-the-loop or agent-assisted NotebookLM sync workflow
- persist the source map cleanly
- detect drift between local segments and recorded sync state

Suggested outputs:
- source map update command(s)
- explicit pending/synced/drifted states
- clear manual handoff file format

Exit criteria:
- every local segment has a visible sync state
- source identity can be resumed safely across runs

## Phase 3: Make `generate` recipe-driven

Goals:
- define a small recipe format for slides, audio, and report
- assemble generation requests from synced sources and recipes
- make incomplete preconditions obvious

Suggested outputs:
- recipe loader
- generation request manifest
- run metadata tying requests to a source-map snapshot

Exit criteria:
- recipes are easy to inspect and edit
- generation requests are reproducible from file-backed inputs

## Phase 4: Make `publish` operational

Goals:
- standardize the download intake folder
- copy artifacts into stable local output folders
- keep a publish manifest for traceability

Suggested outputs:
- expected file naming rules per artifact type
- publish manifest with found/missing statuses
- smoke tests for local file movement

Exit criteria:
- outputs land in predictable local paths
- missing artifacts are visible without reading logs

## Phase 5: Add guardrails, not framework

Goals:
- add focused tests around the stage boundaries
- improve docstrings, examples, and failure modes
- keep the repo narrow as functionality grows

Suggested outputs:
- smoke tests for the four stages
- fixture corpus for pack/sync/generate/publish flows
- lightweight lint/format config only if it earns its keep

Exit criteria:
- contributors can change one stage without decoding a framework
- agentic workflows can inspect artifacts and resume work reliably
