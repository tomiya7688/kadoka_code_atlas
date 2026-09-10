# Comment Generator

## Goal
Add useful source-code comments automatically while preserving program behavior.

## Languages
Initial targets: Python, GDScript, C#, Java. A fifth language may later be Ruby or C.

## Behavior
- Parse source using the language adapter layer.
- Identify structures that benefit from comments: modules, classes, methods/functions, non-obvious branches, and important state/data transformations.
- Generate comments without rewriting unrelated code.
- Preserve formatting as much as practical.
- Never change executable semantics as part of comment insertion.

## Analysis boundary
Deterministic structure extraction belongs in `Src/analyzers/` and `Src/languages/`.
If natural-language comment generation uses an LLM, keep that path separate from deterministic analysis so non-LLM operation remains possible where feasible.

## Output
Modified source code with inserted comments.
