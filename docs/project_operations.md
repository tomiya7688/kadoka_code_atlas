# Project Operations

Kadoka Code Atlas uses GitHub Issues as the task ledger and defaults to `1 Issue ~= 1 PR`.

## Standard flow

```text
Issue
 -> priority + Goal / Required / Acceptance
 -> next_issue.bat (Task Capsule)
 -> remote-delta when concurrent work is possible
 -> Responsibility / Change Routing
 -> search-first working set
 -> implementation
 -> targeted validation + policy check
 -> compact diff / Context Pack when useful
 -> pull_request.bat
 -> CI / review / merge
```

## Task selection
- P0: foundation / blocking correctness
- P1: major capabilities
- P2: extensions / productivity
- P3: future / low-priority improvements

Priority labels are authoritative; `[P0]`-`[P3]` title prefixes are a fallback. Explicit meta/roadmap/umbrella/index items are skipped by automatic selection when actionable work exists.

Issues should contain Goal, Required constraints, Acceptance, Priority, and Out of Scope/Deferred when needed. `next_issue.bat` extracts these into `.codex/next_issue.md`; the original Issue remains authoritative.

## Exploration control

Read in this order:

```text
Task Capsule / metadata
 -> Responsibility Map
 -> search / structure index
 -> target source
 -> matching tests
 -> direct dependencies
 -> detailed docs only if needed
```

Stop broad exploration when Goal, Required, Acceptance, and the working set are sufficient. Reopen only the relevant source of truth if a new ambiguity appears.

## Routing sources
- `docs/responsibility_map.md`: module/file ownership
- `specification/architecture-policy.md`: normative Required/Recommended/Advisory rules
- `docs/current_state.md`: current capabilities and blockers
- `docs/specs/`: feature details, only when routed by the task

Large documents should be entered through heading search (`context.bat doc-index`) rather than unconditional full reads.

## Source Structure Index
`context.bat structure-index` emits a deterministic Python symbol/import index for `Src/` and `tools/`. It is a fallback routing index; richer Common IR/call/dependency analysis from Code Atlas should replace or augment it as the project matures.

Prefer bounded expansion:

```text
target symbol -> direct relations -> matching tests -> deeper graph only if needed
```

Fan-in/fan-out/cycles are impact-routing signals, not automatic design verdicts.

## Remote Delta First
Use `context.bat remote-delta` when another AI/chat/developer may have changed remote state. Inspect ahead/behind, commit subjects, changed files, shortstat, then the bounded diff excerpt. Read full changes only when the current task intersects them.

`remote-delta --ff` is explicit. It refuses dirty/diverged state and only performs a fast-forward.

## Context Pack
`context.bat context-pack` creates `.codex/context_pack.md` from the current Task Capsule, changed files, validation plan, compact diff, and remote status. It is temporary derived context, not a specification; regenerate it instead of accumulating old packets.

## Repository profile
`context.bat profile` reports repository statistics, approximate full-read token cost, file types, and largest text files. Use it to identify context hotspots, not as a quality score.

## Compact diff
`context.bat compact-diff` returns changed-file status, shortstat, and commit subjects. This is the default handoff/PR summary input. Full diff is still used for actual review or ambiguity when needed.

## Validation Routing
`context.bat validation-plan` maps changed files to useful evidence.

- logic: targeted tests -> regression -> broader suite when baseline permits
- architecture: targeted tests + `policy-check`
- GUI: headless behavior first; visual confirmation when visual correctness is Acceptance
- packaging: tests -> build -> artifact smoke when source checks are insufficient
- generated/bulk changes: reproducible transform / dry-run / representative validation
- random/time-dependent behavior: fixed input/seed/time bound + structured observation

A command that checks zero relevant targets is not evidence. Successful logs stay compact; failures may expand around the failure. Anything not checked is `Unverified`.

## Policy Routing
Normative rules live in `specification/architecture-policy.md`. `context.bat policy-check` checks only mechanically useful rules and distinguishes confirmed errors from warnings/review signals. Semantic architecture remains a targeted review task.

A Required-rule exception records rule, reason, scope, mitigation, removal/review condition, and source-of-truth reference.

## Information responsibilities
- README: human overview
- AI_CONTEXT: compact AI routing
- Current State: capabilities / blockers
- Responsibility Map: ownership routing
- docs: explanation / feature design
- specification: normative rules
- Issues: requirements / priority / incomplete work
- source + tests: implemented behavior
- `.codex/` and generated reports/diagrams: derived artifacts

Do not duplicate the same detailed specification across these surfaces.

## Commands
Windows: `context.bat <command>`; Linux/macOS: `./context.sh <command>`.

Available context commands:
- `profile`
- `doc-index`
- `remote-delta`
- `compact-diff`
- `structure-index`
- `validation-plan`
- `policy-check`
- `context-pack`

`next_issue.bat` creates the priority-first Task Capsule. `pull_request.bat` performs the low-context validation/commit/push/PR flow.

## Adopted methods
The project adopts the applicable high-value methods from `ai-context-reducer` and UPD policy practice: compact AI entrypoint, Current State, Task Capsule/Context Pack, Search-first/Read-second, exploration stop conditions, explicit Out of Scope, priority-first actionable Issue selection, Task/Change Routing, Responsibility Map, Source Structure Index, context profile/budget, Remote Delta First, compact diff, Validation Routing, Policy Routing/rule strength/scoped exceptions, deterministic-first structural analysis, generated/noisy-data exclusion, compact handoff reporting, and clear source-of-truth responsibilities.

We do not maintain a second permanent full-repository analysis framework or an always-on giant call-graph cache. Code Atlas itself should become the richer structure-index provider as its shared analysis matures.
