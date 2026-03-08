# AGENTS.md

This repo is a **narrow pipeline**, not a platform.

## What this repo is for

Turn an Obsidian-driven corpus into a file-backed NotebookLM workflow:

1. `pack` → build `source_pack.json`
2. `sync` → persist `source_map.json`
3. `generate` → emit `generation_request.json`
4. `publish` → normalize downloaded outputs into stable local folders

Phase 1 only targets:
- Obsidian corpus / reading map input
- NotebookLM source sync handoff
- recipe-driven `slides` / `audio` / `report`
- local publish intake

## What this repo is NOT

Do **not** turn this into:
- a generic workflow engine
- a background job runner
- a plugin framework
- a vendor-neutral abstraction layer
- a backward-compatibility museum
- fake NotebookLM automation that pretends more is implemented than actually exists

If a change makes the repo feel “flexible” but harder to read, it is probably the wrong change.

## Top-level language

Prefer these terms everywhere:
- `corpus`
- `segment`
- `recipe`
- `run`

Avoid using `book` / `chapter` as the top-level system model.
If those terms appear, they should stay at the edge for specific inputs, not define the whole architecture.

## Read these first

Before editing code, read:
1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/PLANS.md`
4. `docs/ISSUE_BREAKDOWN.md`

These files are the repo map. Keep them updated when behavior changes.

## Implementation rules

- Keep stage boundaries explicit and file-backed.
- Each stage should have obvious inputs and outputs.
- Prefer small datamodels near the stage logic.
- Prefer parse-at-the-boundary over sprawling validation layers.
- Be honest about stubs, TODOs, and manual handoff steps.
- Add tests for real implemented behavior only.
- Keep the happy path legible from the CLI and fixture tests.

## Expected stage artifacts

Under a chosen work dir, the main artifacts are:
- `source_pack.json`
- `source_map.json`
- `sync_handoff.json`
- `generation_request.json`
- `publish_manifest.json`
- `outputs/slides/`
- `outputs/audio/`
- `outputs/report/`

Do not hide critical state in logs or implicit runtime memory when a stable file should exist.

## File formats

Reading maps use an ordered JSON `segments` list with `source_path` and optional `tags`.

Manual sync updates use a JSON `updates` list with:
- `segment_id`
- `notebooklm_source_id`

Recipe files use a JSON `recipes` list with:
- `name`
- `artifact_kind`
- `prompt_focus`

## Commands

Run stages directly:

```bash
python3 scripts/run_pipeline.py pack --corpus-dir /path/to/corpus --work-dir .work --reading-map /path/to/reading_map.json
python3 scripts/run_pipeline.py sync --work-dir .work --source-ids .work/manual_source_updates.json
python3 scripts/run_pipeline.py generate --work-dir .work --recipes /path/to/recipes.json
python3 scripts/run_pipeline.py publish --work-dir .work --downloads-dir .work/downloads
```

Run the current end-to-end skeleton:

```bash
python3 scripts/run_pipeline.py all --corpus-dir /path/to/corpus --work-dir .work --reading-map /path/to/reading_map.json --source-ids .work/manual_source_updates.json --recipes /path/to/recipes.json --downloads-dir .work/downloads
```

## When making changes

Prefer changes that make these questions easy to answer:
- What stage am I in?
- What file does this stage read?
- What file does this stage write?
- Where is local-vs-NotebookLM identity stored?
- Which part is real, and which part is still a stub?

If you cannot answer those quickly after your change, simplify it.


## Skills
A skill is a set of local instructions to follow that is stored in a `SKILL.md` file. Below is the list of skills that can be used. Each entry includes a name, description, and file path so you can open the source for full instructions when using a specific skill.
### Available skills
- ui-ux-pro-max: UI/UX design intelligence. 50 styles, 21 palettes, 50 font pairings, 20 charts, 9 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui). Actions: plan, build, create, design, implement, review, fix, improve, optimize, enhance, refactor, check UI/UX code. Projects: website, landing page, dashboard, admin panel, e-commerce, SaaS, portfolio, blog, mobile app, .html, .tsx, .vue, .svelte. Elements: button, modal, navbar, sidebar, card, table, form, chart. Styles: glassmorphism, claymorphism, minimalism, brutalism, neumorphism, bento grid, dark mode, responsive, skeuomorphism, flat design. Topics: color palette, accessibility, animation, layout, typography, font pairing, spacing, hover, shadow, gradient. Integrations: shadcn/ui MCP for component search and examples. (file: /Users/tian/.agents/skills/ui-ux-pro-max/SKILL.md)
- skill-creator: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. (file: /Users/tian/.codex/skills/.system/skill-creator/SKILL.md)
- skill-installer: Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). (file: /Users/tian/.codex/skills/.system/skill-installer/SKILL.md)
### How to use skills
- Discovery: The list above is the skills available in this session (name + description + file path). Skill bodies live on disk at the listed paths.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text) OR the task clearly matches a skill's description shown above, you must use that skill for that turn. Multiple mentions mean use them all. Do not carry skills across turns unless re-mentioned.
- Missing/blocked: If a named skill isn't in the list or the path can't be read, say so briefly and continue with the best fallback.
- How to use a skill (progressive disclosure):
  1) After deciding to use a skill, open its `SKILL.md`. Read only enough to follow the workflow.
  2) When `SKILL.md` references relative paths (e.g., `scripts/foo.py`), resolve them relative to the skill directory listed above first, and only consider other paths if needed.
  3) If `SKILL.md` points to extra folders such as `references/`, load only the specific files needed for the request; don't bulk-load everything.
  4) If `scripts/` exist, prefer running or patching them instead of retyping large code blocks.
  5) If `assets/` or templates exist, reuse them instead of recreating from scratch.
- Coordination and sequencing:
  - If multiple skills apply, choose the minimal set that covers the request and state the order you'll use them.
  - Announce which skill(s) you're using and why (one short line). If you skip an obvious skill, say why.
- Context hygiene:
  - Keep context small: summarize long sections instead of pasting them; only load extra files when needed.
  - Avoid deep reference-chasing: prefer opening only files directly linked from `SKILL.md` unless you're blocked.
  - When variants exist (frameworks, providers, domains), pick only the relevant reference file(s) and note that choice.
- Safety and fallback: If a skill can't be applied cleanly (missing files, unclear instructions), state the issue, pick the next-best approach, and continue.
