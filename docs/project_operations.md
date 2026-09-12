# Project operations

Kadoka Code Atlas は Issue を唯一のタスク台帳として扱い、原則 `1 Issue ~= 1 PR` で進めます。運用は `ai-context-reducer` の原則を適応し、必要情報を先に選別してから AI へ渡します。

## Standard flow

```text
conversation / idea
  -> GitHub Issue
  -> priority
  -> next_issue.bat
  -> .codex/next_issue.md
  -> scoped implementation
  -> targeted validation
  -> pull_request.bat
  -> pytest
  -> compact change summary
  -> PR
  -> CI / review
  -> merge
```

## Priority
- P0: プロジェクト成立に必要な基盤・アーキテクチャ・主要入口
- P1: 主要機能
- P2: 拡張・利便性改善
- P3: 将来案・低優先改善

priority label がある場合は label を正とします。label が無い既存 Issue ではタイトル先頭の `[P0]`〜`[P3]` をフォールバックとして扱います。

## Issue rules
Issue には可能な限り次を含めます。

- Goal: 何を達成するか
- Required: 守る制約・必要要件
- Acceptance Criteria: 何をもって完了とするか
- Priority
- 関連 spec / subsystem が明確ならその参照

Issue が大きすぎる場合は子 Issue に分けます。実装中に無関係なリファクタを混ぜません。

## Context reduction rules
- 最初に全 repository / 全 docs / 全 Issues を読まない
- `.codex/next_issue.md` がある場合はその Issue だけを現在タスクとする
- search / routing で対象を絞ってから source を読む
- Goal / Required / Acceptance と必要な working set が揃ったら探索を止める
- 要約は索引として使い、不足時だけ原典へ戻る
- full diff は通常読まず、changed files / diff stat を先に確認する
- 成功ログ全文は保持せず、失敗時だけ必要範囲を読む

## Task routing

| Task | Source | Tests | Docs |
|---|---|---|---|
| language parsing / adapter | `Src/languages/` | language-specific tests | related spec |
| relationship / flow analysis | `Src/analyzers/` | analyzer / graph tests | diagram / analysis spec |
| class/sequence/etc generation | `Src/generators/` | generator tests | `docs/specs/diagrams.md` |
| comment generation | generators + language adapters | comment tests | `docs/specs/comment_generator.md` |
| output formats | `Src/renderers/` | renderer tests | diagram/output spec |
| design evaluation | `Src/evaluators/` | evaluator tests | `docs/specs/design_evaluation.md` |
| CI analysis | analyzer / tooling area | targeted CI tests | `docs/specs/ci_analyzer.md` |
| issue / PR automation | `tools/`, root `*.bat` | tool tests | this document |
| architecture boundary | relevant source + docs | affected tests | `docs/architecture/` |

## Change routing
変更カテゴリから最初に読む場所を決めます。

- parser change: language adapter -> Common IR contract -> matching tests
- IR change: IR contract -> all direct consumers -> focused compatibility tests
- analyzer change: analyzer -> generator/evaluator consumers only if interface changes
- generator change: generator -> renderer contract only if output model changes
- renderer change: renderer only; analyzer を読まない
- GUI change: UI -> Process boundary -> headless behavior tests first
- data access change: Data boundary -> Process Messenger contract

## Validation routing
### Source / algorithm change
1. matching targeted tests
2. nearby regression tests
3. PR 前に full `pytest`

### Architecture / routing docs only
- link / path consistency
- examples and invariants review
- affected tooling tests when behavior is changed

### GUI / interactive change
- headless / application logic tests first
- Acceptance に表示確認が必要な場合だけ visual confirmation

### Build / packaging change
- unit tests
- build
- packaged artifact smoke when applicable

実行できない検証は `Unverified` として PR に明記します。

## Remote delta
複数 AI / chat / developer が同じ remote を触る場合、実装前に full diff ではなく次を優先します。

1. recent commit summary
2. changed files
3. diff stat
4. 必要なファイルだけ詳細確認

競合可能性が判明した場合だけ詳細 diff へ進みます。

## Low-context tools
### `next_issue.bat`
- open Issues を取得
- priority で1件だけ選ぶ
- deterministic に短い要約を作る
- `.codex/next_issue.md` へ必要 context を出す

### `pull_request.bat`
- `pytest` を実行
- work branch 上で commit
- changed-file names / diff statistics だけで compact PR summary を作る
- push / PR 作成

失敗・曖昧さがある場合だけ full diff / log を追加で確認します。

## Adoption scope
`ai-context-reducer` から採用するもの:
- compact AI entrypoint
- search first / read second
- exploration stop condition
- Source of Truth
- Task / Change Routing
- Validation Routing
- Remote Delta First
- unrelated refactor separation
- Unverified areas

現時点で常設しないもの:
- 大規模な生成 Source Structure Index
- 常時更新する巨大 call graph cache
- 複雑な要約キャッシュ

これらは repository 規模と反復コストが増え、維持費より削減効果が大きくなった時点で導入します。
