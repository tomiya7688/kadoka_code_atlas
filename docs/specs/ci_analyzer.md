# CI Analyzer

## Goal
Provide analysis suitable for CI pipelines so architectural or code-quality regressions can be detected automatically.

## Responsibilities
- Run deterministic analyzers non-interactively.
- Produce stable machine-readable results suitable for CI consumption.
- Support pass/fail thresholds without coupling CI logic to UI code.
- Reuse the same intermediate analysis model used by local diagram/table generation.

## Candidate checks
- Dependency/call-graph changes
- Excessive coupling or fan-in/fan-out
- Newly introduced cycles
- Structural complexity growth
- Design-evaluation score regressions
- Parser/analyzer failures for supported languages

## Output
Human-readable summary plus a machine-readable result format. Exit status should reflect configured CI failure conditions.

## Boundary
CI should default to deterministic checks. Any LLM-assisted evaluation must be optional and clearly labeled so reproducible CI remains possible.
