# Kadoka Code Atlas — Codex Context

## Purpose
Kadoka Code Atlas is a source-code analysis toolkit that generates diagrams, tables, comments, evaluations, and CI-oriented analysis results.

## Supported languages
Primary targets:
- Python
- GDScript
- C#
- Java

Candidate fifth language:
- Ruby or C

## Repository structure
- `Src/analyzers/` — deterministic/static analysis
- `Src/generators/` — logical output generation
- `Src/renderers/` — Mermaid/text/other rendering
- `Src/evaluators/` — design/code quality evaluation
- `Src/languages/` — language-specific parsing and adapters
- `app.py` — application entry point
- `run.bat` — Windows launcher

## Architecture rules
- Keep language-specific parsing inside `Src/languages/`.
- Prefer language-independent intermediate representations between parsing and generation.
- Keep analysis logic independent from UI and rendering.
- Prefer deterministic static analysis whenever practical.
- LLM-assisted or dynamic analysis must be explicitly separated from deterministic static analysis.
- Generators produce logical results; renderers format them.
- Reuse shared analysis results across multiple diagram generators instead of reparsing the same code independently.

## Output policy
- Diagram output defaults to Mermaid.
- Comment generation writes comments into source code.
- Tables should use simple machine-readable structures where practical.

## Major planned features
- Comment generator
- Class diagram generator
- Object diagram generator
- Sequence diagram generator
- Package diagram generator
- Use-case diagram generator
- Communication diagram generator
- Activity diagram generator
- Component diagram generator
- Deployment diagram generator
- State-machine diagram generator
- Timing diagram generator
- Call graph generator
- Class responsibility table generator
- CI analyzer
- Design evaluation

## Class-diagram grouping rule
Default to caller-centered diagrams. If one class is referenced by many callers, generate a dedicated callee-centered diagram for that heavily referenced class.

## Current issue context
If `.codex/next_issue.md` exists, treat the issue described there as the current highest-priority task. Read that file immediately after this one. Do not fetch or load unrelated issues unless the selected issue requires them.

## Context discipline
This file intentionally stays short. Read only the relevant file under `docs/specs/` for the feature being modified. Do not load every feature specification unless the task actually spans them.

## License
MIT
