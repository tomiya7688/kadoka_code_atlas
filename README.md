# Kadoka Code Atlas

Kadoka Code Atlas は、ソースコードの構造・振る舞い・依存関係・責務を解析し、図表・コメント・設計評価として可視化するためのツール群です。

目的は、コードを読む前に「何があるか」「どこから呼ばれるか」「何に依存するか」「どこが複雑か」を短時間で把握できる状態を作ることです。

## Main capabilities

主な対象は次の通りです。

- コメント生成
- クラス図 / オブジェクト図
- シーケンス図 / コミュニケーション図
- 状態遷移図 / アクティビティ図 / タイミングチャート
- ユースケース図
- パッケージ図 / コンポーネント図 / デプロイメント図
- コールグラフ
- クラス責務表
- CI 解析
- 設計評価

図表の標準出力は Mermaid とし、PlantUML 等は Renderer の差し替えで追加できる構造を目指します。コメント生成は基本的に元ソースへ追記します。

## Analysis targets

主要な解析対象言語:

- Python
- GDScript
- C#
- C++
- Java
- Go

最初の解析実装対象は Python です。言語固有処理は境界へ閉じ込め、中央の解析・生成・評価処理は可能な限り言語非依存にします。

## Core architecture

```text
Source
  -> Language Adapter / Parser
  -> Common IR
  -> Analyzer / Generator / Evaluator
  -> Logical Output
  -> Renderer
  -> Mermaid / PlantUML / text / table
```

基本ルール:

- 言語固有 parser / AST / OSS 型は `Src/languages/` の外へ漏らさない
- Common IR はデータのみを保持する
- Analyzer / Generator / Evaluator は言語固有 AST へ直接依存しない
- Renderer は出力形式を担当し、解析ロジックを持たない
- 解析結果は複数の図・表・評価機能で再利用する

アプリケーション全体の責務分離には UPD Commander Base Design の UI / Process / Data 境界を採用します。

- UI: 入力・表示・ユーザー向け起動フロー
- Process: 解析・生成・評価のオーケストレーション
- Data: source / config / file / external data access

Commander は呼び出しの交通整理のみ、Messenger は層間通信のみを担当します。詳細は [`docs/architecture/upd_commander.md`](docs/architecture/upd_commander.md) を参照してください。

## Repository structure

```text
Src/
  analyzers/      # static / deterministic analysis
  generators/     # logical output generation
  renderers/      # Mermaid / text / other formatting
  evaluators/     # design / code quality evaluation
  languages/      # language-specific adapters

tests/            # automated tests
tools/            # project-operation helpers
docs/specs/       # feature specifications
docs/architecture/# architecture rules
app.py             # application entry point
run.bat            # Windows launcher
```

## Project operations

設計・機能追加・修正・評価は GitHub Issue をタスク台帳として管理し、原則 `1 Issue ~= 1 PR` で進めます。

低コンテキスト運用の標準フロー:

```text
Issue
  -> next_issue.bat
  -> one compact current-task context
  -> scoped implementation
  -> targeted validation
  -> pull_request.bat
  -> pytest
  -> compact diff summary
  -> PR
```

- `next_issue.bat`: 最優先 Issue を1件だけ選び `.codex/next_issue.md` を生成
- `pull_request.bat`: pytest、commit、changed-file / diff-stat ベースの要約、push、PR作成
- `AI_CONTEXT.md`: AI が最初に読む小さい routing index

詳細は [`docs/project_operations.md`](docs/project_operations.md) を参照してください。

## AI context policy

AI に repository 全体を無条件で読ませるのではなく、Issue・routing・検索で必要情報を先に絞ります。

- Search first, read second
- Goal / Required / Acceptance が揃ったら探索を止める
- unrelated refactor を混ぜない
- full diff / large logs / all docs / all Issues を通常コンテキストへ入れない
- 要約は索引として扱い、不足時だけ原典へ戻る
- 正確性をコンテキスト削減量より優先する

この方針は `ai-context-reducer` を参考に Kadoka Code Atlas 向けへ適応しています。外部リポジトリは実行時必須依存ではありません。

## Specifications

README は概要だけを保持します。個別機能の要件・Acceptance Criteria は `docs/specs/` と GitHub Issues を Source of Truth とします。

AI / Codex 向け入口は `AI_CONTEXT.md` と `AGENTS.md` です。

## License

MIT License

## Status

初期実装・アーキテクチャ整備中です。
