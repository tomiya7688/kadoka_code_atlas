# Feature Specifications

These files are intentionally split so Codex can load only the context required for the current task.

## Read-on-demand map
- Comment generation → `comment_generator.md`
- UML/graph diagram generation → `diagrams.md`
- Class responsibility table → `class_responsibility_table.md`
- CI integration and checks → `ci_analyzer.md`
- Design-quality evaluation → `design_evaluation.md`

## Context rule
Start with the repository-root `AGENTS.md`. Then read only the relevant specification above. Load multiple specs only when a task genuinely crosses those boundaries.

When a feature grows enough that its section becomes large, split it into its own spec rather than expanding the always-loaded context.
