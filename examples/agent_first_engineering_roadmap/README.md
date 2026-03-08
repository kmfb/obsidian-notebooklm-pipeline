# Agent-first engineering roadmap bundle

This folder is a thin example bundle for an Obsidian-first roadmap workflow.

It keeps the repo honest:
- no raw article bodies are checked in here
- `reading_map.json` is the stage input for `pack`
- `source_index.json` adds hierarchy and planning context for humans and agents
- `recipes.json` shows the current recipe fields that flow into guarded `nlm` create commands

To use it against a real corpus:
1. mirror the `source_path` values inside your Obsidian corpus
2. run `pack` with `reading_map.json`
3. run `sync`, then replace placeholder values in `manual_source_updates.example.json`
4. run `generate --notebook-id ...` with `recipes.json`

All paths are repo-local examples, not shipped content.
