# Agent-first engineering roadmap bundle

This folder is a thin example bundle for an Obsidian-first roadmap workflow.

It keeps the repo honest:
- no raw article bodies are checked in here
- `reading_map.json` is the stage input for `pack`
- `source_index.json` adds hierarchy and planning context for humans and agents
- `recipes.json` shows the current recipe fields that flow into guarded `nlm` create commands

To use it against a real corpus:
1. mirror the `source_path` values inside your Obsidian corpus
2. start with:

   ```bash
   python3 scripts/run_pipeline.py reading-map-run \
     --corpus-dir /path/to/corpus \
     --work-dir .work \
     --reading-map examples/agent_first_engineering_roadmap/reading_map.json \
     --recipes examples/agent_first_engineering_roadmap/recipes.json
   ```

3. review `.work/sync_handoff.json`, then copy real NotebookLM source IDs into `.work/manual_source_updates.json`
4. rerun `reading-map-run` with `--notebook-id ...` and add `--execute-generate` only when you want it to call `nlm`
5. place downloaded outputs under `.work/downloads/` and rerun `reading-map-run` to publish them locally

All paths are repo-local examples, not shipped content.
