# AI Context

Kadoka Code Atlas で AI が最初に読む小さい索引です。詳細仕様は複製しません。

## Source of Truth
- Current task: GitHub Issue。`.codex/next_issue.md` があればその1件を優先する。
- Overview: `README.md`
- AI / coding rules: `AGENTS.md`
- Architecture: `docs/architecture/upd_commander.md`
- Feature specs: `docs/specs/`
- Operations: `docs/project_operations.md`
- Source / tests: `Src/`, `tools/`, `tests/`

## Read First
1. `AI_CONTEXT.md`
2. `.codex/next_issue.md`（存在する場合）
3. `AGENTS.md`
4. 指定された関連 spec
5. 変更対象 source と対応 test

## Working Rules
- Goal / Required / Acceptance が揃ったら追加探索を止める。
- Search first, read second。
- unrelated refactor を混ぜない。
- 全 docs / 全 Issues / full diff を無条件に読まない。
- 要約で不足する場合だけ原典へ戻る。
- 正確性をコンテキスト削減量より優先する。

## Routing
- language adapter -> `Src/languages/`
- analysis -> `Src/analyzers/`
- logical generation -> `Src/generators/`
- output formatting -> `Src/renderers/`
- design evaluation -> `Src/evaluators/`
- issue / PR workflow -> `tools/`, `*.bat`

## Architecture Constraints
- Common IR はデータのみを持つ。
- 言語固有 AST は language 境界から上へ漏らさない。
- Renderer に解析ロジックを持たせない。
- UI / Process / Data の層越えアクセスを避ける。
- Commander は呼び出しの交通整理のみ、Messenger は層間通信のみを担当する。

## Validation
変更に必要な targeted tests を先に行い、PR 前は全体 `pytest` を実行する。実行できなかった検証は Unverified として明示する。

## Low-context Commands
- `next_issue.bat`: 最優先 Issue を1件だけ `.codex/next_issue.md` にする。
- `pull_request.bat`: pytest -> commit -> compact diff summary -> push -> PR。

`ai-context-reducer` と `upd-commander-base-design` は設計参考元であり、実行時必須依存ではありません。
