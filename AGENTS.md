# Kadoka Code Atlas — Agent Guide

## Start here
Read `AI_CONTEXT.md` first. It is the compact routing index for this repository.

If `.codex/next_issue.md` exists, treat the Issue described there as the current highest-priority task. Do not fetch or load unrelated Issues unless the selected Issue requires them.

Detailed project operations are in `docs/project_operations.md`. UPD layer rules are in `docs/architecture/upd_commander.md`.

## Purpose
Kadoka Code Atlas is a source-code analysis toolkit that generates diagrams, tables, comments, evaluations, and CI-oriented analysis results.

## Primary analysis targets
- Python
- GDScript
- C#
- C++
- Java
- Go

Python is the first analysis target. Implementation choices must not make the architecture dependent on a single analysis language.

## Repository structure
- `Src/analyzers/` — deterministic/static analysis
- `Src/generators/` — logical output generation
- `Src/renderers/` — Mermaid/text/other rendering
- `Src/evaluators/` — design/code quality evaluation
- `Src/languages/` — language-specific parsing and adapters
- `tools/` — project-operation helpers
- `app.py` — application entry point
- `run.bat` — Windows launcher

## Architecture rules
- Keep language-specific parsing inside `Src/languages/`.
- Prefer language-independent intermediate representations between parsing and generation.
- Common IR stores data only; do not add analysis, evaluation, rendering, or convenience behavior to it.
- Keep analysis logic independent from UI and rendering.
- Prefer deterministic static analysis whenever practical.
- LLM-assisted or dynamic analysis must be explicitly separated from deterministic static analysis.
- Generators produce logical results; renderers format them.
- Reuse shared analysis results across multiple diagram generators instead of reparsing the same code independently.

### UPD boundary
Kadoka Code Atlas adopts the UI / Process / Data separation from UPD Commander Base Design.

- UI: input, presentation, user-facing launch flow
- Process: orchestration, analysis, generation, evaluation
- Data: source/config/file/external data access
- Commander selects what to call and stays thin.
- Messenger handles cross-layer communication and contains no business logic.
- UI must not directly access Data.

See `docs/architecture/upd_commander.md` for the detailed boundary rules.

## Output policy
- Diagram output defaults to Mermaid.
- Comment generation writes comments into source code.
- Tables should use simple machine-readable structures where practical.
- PlantUML and other output formats belong behind renderer boundaries.

## Class-diagram grouping rule
Default to caller-centered diagrams. If one class is referenced by many callers, generate a dedicated callee-centered diagram for that heavily referenced class.

## Low-context workflow
Use `next_issue.bat` before starting general Issue work. It selects one highest-priority Issue and writes `.codex/next_issue.md` deterministically.

Use `pull_request.bat` after completing an Issue. It runs `pytest`, stops on failure, commits local changes, pushes the work branch, and creates a PR using changed-file names and diff statistics for its summary.

Do not load the full diff merely to prepare a PR unless a failure or ambiguity requires inspection.

## Context discipline
- Search first, read second.
- Stop broad exploration when Goal / Required / Acceptance and the working set are sufficient.
- Read only the relevant file under `docs/specs/` for the feature being modified.
- Do not load every feature specification, all Issues, or repository history by default.
- Keep unrelated refactors out of the current Issue.
- If a summary is insufficient for a decision, return to the source of truth.
- Report validation that could not be executed as `Unverified`.

## License
MIT
