# UPD Commander adoption

Kadoka Code Atlas は `upd-commander-base-design` の UI / Process / Data 分離と Commander / Messenger の責務分離を採用します。ただし、外部リポジトリや特定実装への依存は持ちません。

## Layer mapping

### UI Layer
担当:
- GUI / CLI / 起動処理
- ユーザー入力
- 表示設定
- 結果表示・保存操作

UI は解析ロジックを実装せず、Data 層へ直接アクセスしません。

### Process Layer
担当:
- アプリケーション上の処理フロー
- Analyzer / Generator / Evaluator / Renderer のオーケストレーション
- Common IR を利用した言語非依存処理
- 解析結果から次に実行する処理の決定

Process は UI の表示方法や保存先の詳細を知りません。

### Data Layer
担当:
- 解析対象ソース・設定の取得
- ファイル入出力
- キャッシュや永続化
- 外部データアクセス

Data は UI や解析上の業務判断を持ちません。

## Commander
Commander は「どの処理を次に呼ぶか」を決める薄い交通整理役です。

行ってよいこと:
- 要求を受け取る
- 適切な Processing / service を選ぶ
- 必要な層間通信を Messenger に依頼する
- 結果を次の処理へ渡す

行わないこと:
- AST 解析
- graph 計算
- diagram 生成
- Mermaid 文字列生成
- ファイル読み書き
- 複雑な業務判断

## Messenger
Messenger は隣接層との通信契約を担当します。

行ってよいこと:
- command / request / result を送受信する
- 受信内容を自層 Commander へ渡す

行わないこと:
- 解析・評価・描画ロジック
- 呼び出し先 Processing の選定
- データ変換や保存処理

## Dependency rules
基本経路は次です。

```text
UI <-> Process <-> Data
```

原則禁止:

```text
UI -> Data
Data -> UI
UI Processing -> Process Processing
Process Processing -> Data Processing
```

層を越える通信は Messenger または同等の明示的な境界を経由します。

## Existing Kadoka boundaries remain authoritative
UPD は既存の言語・IR・出力境界を置き換えません。次の規則は併存します。

```text
Source
  -> Language Adapter / Parser
  -> Common IR
  -> Analyzer / Generator / Evaluator
  -> Logical Output
  -> Renderer
```

- language-specific parser / OSS 型は language adapter 内へ閉じ込める
- Common IR はデータのみを保持する
- Analyzer / Generator / Evaluator は可能な限り言語非依存にする
- Renderer は Mermaid / PlantUML 等の出力形式だけを担当する

UPD は上記パイプラインをアプリケーション全体の UI / Process / Data 境界へ配置するための上位ルールとして扱います。

## Practical mapping example

```text
UI Commander
  -> Process Messenger
  -> Process Commander
  -> Language Adapter
  -> Common IR
  -> Analyzer / Generator
  -> Renderer
  -> Process Commander
  -> UI Messenger
  -> UI Processing
```

解析対象の読み込みや結果ファイル保存が必要な場合だけ Process から Data Messenger を経由します。

## Review checklist
新しい機能を追加するときは次を確認します。

- UI が解析・保存ロジックを持っていないか
- Process が表示形式・保存先の詳細へ依存していないか
- Data が解析判断や UI 判断を持っていないか
- Commander / Messenger が肥大化していないか
- Common IR に処理ロジックが追加されていないか
- Renderer に解析処理が入り込んでいないか

例外が必要な場合は、理由と影響範囲を Issue / PR に明示します。
