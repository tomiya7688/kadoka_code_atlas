# AST / Semantic backend conformance fixture

Issue #131 defines a versioned fixture used to compare parser and semantic backends
without exposing backend-specific AST or symbol objects outside a language adapter.

## Contract

The fixture lives under `tests/fixtures/backend_conformance/`.

- `manifest.json` identifies the six primary source-language fixtures and the
  capability probes each one contains.
- `expected_common_ir_v1.json` is the language-independent semantic golden.
- one source file per language expresses the same core structure where the
  language permits it.

The shared core is:

```text
BaseWorker
  ^
  |
Worker
  + run(item)
      -> helper(item)
      -> helper(item)
  + helper(item)
  + async_probe(item)
  + nested_probe(item)
```

Each fixture also contains at least one import/dependency reference. Generic,
async and nested-scope behavior are capability probes because not every language
expresses those concepts in the same way. For example, GDScript has typed
containers rather than user-defined generic classes.

## What the golden intentionally excludes

The golden contract compares Common IR semantics, not parser implementation
details. It therefore excludes source line offsets, indentation, AST node names,
Roslyn syntax kinds, tree-sitter node types, Clang cursor kinds, token IDs and
backend-specific diagnostic objects.

A backend may preserve richer information internally, but a Language Adapter
must normalize it before analyzers, generators, evaluators or renderers see it.

## Evaluation flow

```text
fixture source
  -> candidate parser / semantic backend
  -> Language Adapter
  -> ModuleIR
  -> semantic projection
  -> expected_common_ir_v1.json
```

The exact parser can differ by language. A backend is not preferred merely
because it is implemented in Python.

## CI usage

`tests/test_backend_conformance_fixture.py` validates the fixture schema on
every normal CI run and executes the current Python project adapter against the
golden semantic subset. Language-specific evaluation issues (#132-#137) should
reuse this fixture and record unsupported capabilities explicitly rather than
inventing normalized facts.

When a future Common IR field is added for generics, async semantics or symbol
resolution, the fixture contract must be versioned rather than silently changing
v1 expectations.
