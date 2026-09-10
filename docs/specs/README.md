# Feature Specifications

These files are intentionally split so Codex can load only the context required for the current task.

## Read-on-demand map
- Comment generation → `comment_generator.md`
- UML/graph diagram generation → `diagrams.md`
- Class responsibility table → `class_responsibility_table.md`
- CI integration and checks → `ci_analyzer.md`
- Design-quality evaluation → `design_evaluation.md`

## Issue label routing
`tools/next_issue.py` maps `spec:*` labels on the selected GitHub Issue to the minimum relevant spec files and writes those paths into `.codex/next_issue.md`.

Recommended labels:
- `spec:comment-generator` → `comment_generator.md`
- `spec:class-diagram`, `spec:sequence-diagram`, `spec:call-graph`, and other diagram labels → `diagrams.md`
- `spec:class-responsibility-table` → `class_responsibility_table.md`
- `spec:ci-analyzer` → `ci_analyzer.md`
- `spec:design-evaluation` → `design_evaluation.md`

An Issue may carry multiple `spec:*` labels when it genuinely spans multiple feature areas. If no recognized `spec:*` label is present, Codex is instructed to inspect only the minimum implementation files needed and not to load all specifications.

## Context rule
Start with the repository-root `AGENTS.md`. Then read only the relevant specification above. Load multiple specs only when a task genuinely crosses those boundaries.

When a feature grows enough that its section becomes large, split it into its own spec rather than expanding the always-loaded context.
