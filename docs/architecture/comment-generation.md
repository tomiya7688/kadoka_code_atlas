# Comment Generation Architecture

This document defines the source-of-truth comment-generation pipeline for the Python implementation.

## Canonical model

`Src.models.comments.CommentCandidate` is the only shared comment-candidate contract.

A candidate contains only normalized source-rewrite metadata and proposed comment text:

- target kind
- target name
- source line
- indentation
- proposed text

Language parser AST / syntax-node objects must not cross this boundary.

## Production pipeline

The normal CLI / GUI / `ApplicationService` path is:

```text
Source text
  -> CommentAdapter
  -> ParsedSource[CommentCandidate]
  -> CommentGenerator
  -> CommentTextBackend
  -> source rewrite
```

Responsibilities:

- `CommentAdapter`: language-specific source inspection and candidate extraction.
- `ParsedSource` / `CommentCandidate`: normalized boundary models.
- `CommentTextBackend`: replace or preserve proposed comment text without changing adapters.
- `CommentGenerator`: orchestration, language selection, backend invocation, and source insertion.
- `ApplicationService`: I/O-facing orchestration only.

The default `RuleBasedCommentBackend` preserves the deterministic text proposed by the adapter. A future LLM or other text backend may be injected without changing the language adapters.

## Common IR helper

`RuleBasedCommentGenerator` has a narrower role:

```text
Source text
  -> Common IR LanguageAdapter
  -> ModuleIR
  -> RuleBasedCommentGenerator
  -> CommentCandidate
```

It is a pure Common-IR-to-candidate transformation helper. It does not parse source text, select language adapters, choose a text backend, or rewrite source files.

The Python `apply_python_comments()` function remains a compatibility/source-rewrite helper for this IR-derived path. It consumes the same canonical `CommentCandidate` model; it does not define a second candidate type.

## Boundary rules

- `Src.models.comments.CommentCandidate` is the candidate source of truth.
- Do not define another `CommentCandidate` dataclass in generators, languages, or process code.
- Comment adapters implement `Src.process.contracts.CommentAdapter`, not the Common IR `LanguageAdapter` contract.
- Common IR remains data-only and contains no comment-generation behavior.
- Language-specific parser types remain inside the corresponding language adapter.
- Text-backend replacement must not require adapter changes.
- Source rewrite metadata such as indentation and insertion line belongs to the comment candidate boundary, not to Common IR.

## Compatibility

Existing Python, C#, C++, GDScript, Java, and Go comment-generation behavior remains on the production `CommentGenerator` path. The Common IR helper exists for reuse and conformance work, not as a competing production pipeline.
