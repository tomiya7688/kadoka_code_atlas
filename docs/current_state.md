# Current State

This file is a compact snapshot of what is currently present in the repository. It is an index, not a specification. Update it when a major capability or constraint changes.

## Available foundation

- Python and C# language-adapter code is present under `Src/languages/`.
- Common analysis models / IR and call-graph analysis are present under `Src/analyzers/` and `Src/models/`.
- Comment-generation implementations and call-graph generation helpers are present under `Src/generators/`.
- Mermaid call-graph rendering is present under `Src/renderers/`.
- Automated tests cover call graph, comments, public exports, and project-operation tooling.
- `app.py`, `run.bat`, packaging metadata, and GitHub Actions provide the current launch/build foundation.
- `next_issue.bat` and `pull_request.bat` provide the low-context Issue -> PR workflow.
- `context.bat` / `context.sh` expose repository profile, remote delta, compact diff, structure index, validation planning, policy checks, and Context Pack generation.

## Architecture direction

- Language-specific parsing stays behind language adapters.
- Common IR is the interchange boundary for language-independent analysis.
- Analysis / generation / evaluation and output rendering remain separate responsibilities.
- UI / Process / Data boundaries follow the Kadoka adaptation of UPD Commander Base Design.
- Commander and Messenger are orchestration/communication roles, not locations for real processing.
- Mermaid is the default diagram output; other formats belong behind renderer boundaries.

## Known limitations / active work

- Most planned UML generators and design evaluators are still Issue-driven future work.
- Python is the first implementation target for most new analysis features even though other language adapters are planned or partially present.
- GUI work is still tracked as a P0 area rather than a completed product surface.
- Full-suite pytest baseline has an active compatibility problem around the legacy/current comment-generation API; see Issue #23 until resolved.
- The architecture policy checker intentionally distinguishes confirmed errors from review warnings so existing transitional code can be migrated without pretending every architectural rule is mechanically provable.

## Current highest-level goals

1. Stabilize Common IR and dependency boundaries.
2. Keep the project usable by humans and AI without full-repository rereads.
3. Build shared analysis primitives once, then reuse them across diagrams, tables, CI analysis, and design evaluation.
4. Keep language, UI, storage, and renderer dependencies at replaceable boundaries.

## Maintenance rule

Do not turn this file into a changelog. Keep only current capabilities, important constraints, known blockers, and near-term architectural state. Historical detail belongs in Git history, Issues, and PRs.
