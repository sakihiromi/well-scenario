# Well-Scenario グラフ表示・人手アノテーション機能 実装完了

## 実装内容サマリー

well-scenarioプロジェクトにグラフ表示と人手アノテーション機能を追加しました。以下の機能が実装されています：

- **グラフ表示**: 4つのメトリクス（威圧度、逸脱度、発言無効度、偏り度）のスコアを折れ線グラフで可視化
- **人手アノテーション**: グラフ上の点をドラッグして手動でスコアを調整
- **データ分離保存**: 機械アノテーションと人手アノテーションを別々にJSON保存

## 実装したファイル

### バックエンド

#### [app.py](file:///Users/saki/lab/US/well-scenario/app.py#L237-L296)

新しいAPIエンドポイント`POST /api/output/<filename>/annotations`を追加しました。

**主な機能:**
- 人手アノテーションをJSON形式で受け取る
- 既存のJSONファイルを読み込み、`machine_annotations`と`human_annotations`を分離
- メタデータに`last_human_annotation`タイムスタンプを追加
- 更新されたデータをファイルに書き戻す

**自動スキーマ移行:**
- 既存の`metrics`フィールドを自動的に`machine_annotations`にリネーム
- 後方互換性を維持しながら新しいスキーマに対応

### フロントエンド

#### [static/chart_editor.js](file:///Users/saki/lab/US/well-scenario/static/chart_editor.js)

Chart.jsを使用したグラフエディタークラスを新規作成しました。

**主な機能:**
- 4つのメトリクス別に折れ線グラフを生成
- 機械アノテーション（青い実線）と人手アノテーション（赤い点線）を区別表示
- `chartjs-plugin-dragdata`プラグインでドラッグ操作を実装
- スコアを0-9の範囲内に自動制限
- 変更状態を管理し、保存ボタンの有効/無効を切り替え
- 人手アノテーションをAPIに送信して保存

**技術詳細:**
- Chart.jsのバージョン: 4.4.1
- プラグイン: chartjs-plugin-dragdata 2.2.5
- データ構造の柔軟な処理（既存の`metrics`と新しい`machine_annotations`の両方に対応）

#### [templates/index.html](file:///Users/saki/lab/US/well-scenario/templates/index.html#L6-L8)

HTMLに以下を追加：
- Chart.jsとドラッグプラグインのCDNリンク
- グラフセクション（4つのcanvas要素）
- 保存ボタン
- 凡例と使い方のガイド

#### [static/script.js](file:///Users/saki/lab/US/well-scenario/static/script.js#L243-L251)

`displayScenario`関数にグラフ初期化処理を追加しました。シナリオ表示後、自動的にグラフエディターを初期化します。

#### [static/style.css](file:///Users/saki/lab/US/well-scenario/static/style.css#L439-L596)

グラフセクションのスタイリングを追加：
- 2x2グリッドレイアウト（4つのグラフ）
- 凡例のスタイル（実線と点線の区別）
- 保存ボタンのスタイル
- レスポンシブ対応（モバイルで1カラムに切り替え）

### ドキュメント

#### [README.md](file:///Users/saki/lab/US/well-scenario/README.md)

READMEを更新し、以下を追加：
- 主な機能一覧にグラフ表示と人手アノテーション機能を追加
- フロントエンド機能セクションにグラフ機能の詳細説明を追加
- 新しいAPIエンドポイント`POST /api/output/<filename>/annotations`のドキュメント
- JSONスキーマの更新（`machine_annotations`と`human_annotations`の分離）
- データフィールドの詳細説明

## JSONデータ構造

### 変更前（既存のスキーマ）

```json
{
  "scenario": [
    {
      "speaker": "田中",
      "text": "...",
      "metrics": {
        "威圧度": {"score": 2, "reason": "..."}
      }
    }
  ]
}
```

### 変更後（新しいスキーマ）

```json
{
  "metadata": {
    "last_human_annotation": "2024-12-14T16:30:00.000000"
  },
  "scenario": [
    {
      "speaker": "田中",
      "text": "...",
      "machine_annotations": {
        "威圧度": {"score": 2, "reason": "..."}
      },
      "human_annotations": {
        "威圧度": {
          "score": 3,
          "edited_at": "2024-12-14T16:30:00.000000",
          "note": "ユーザーによる調整"
        }
      }
    }
  ]
}
```

## 動作確認

### サーバー起動

Teams2wb conda環境でFlaskサーバーが正常に起動することを確認：

```bash
conda activate teams2wb && python app.py
```

サーバーはポート5001で起動し、以下のログが表示されます：

```
Well-Scenario サーバー起動中...
URL: http://localhost:5001
モデル: gpt-4o-mini
サニタイズモード: 無効
 * Running on http://localhost:5001
```

### 機能確認

実装した機能は以下の流れで動作します：

1. **シナリオ生成**: ユーザーが会議設定を入力してシナリオを生成
2. **グラフ表示**: 生成されたシナリオの下にグラフセクションが自動表示される
3. **スコア調整**: グラフ上の赤い点線（人手アノテーション）をドラッグしてスコアを変更
4. **保存**: 保存ボタンをクリックして変更をJSONファイルに保存
5. **読み込み**: 保存されたファイルを再度開くと、人手アノテーションが反映される

## 技術的なハイライト

### 後方互換性

既存のJSONファイル（`metrics`フィールドを使用）との互換性を維持しながら、新しいスキーマに移行できるようにしました。

**自動移行ロジック:**
```python
if 'metrics' in utterance and 'machine_annotations' not in utterance:
    utterance['machine_annotations'] = utterance.pop('metrics')
```

フロントエンドでも柔軟に対応：
```javascript
const machineAnnotations = utterance.machine_annotations || utterance.metrics || {};
```

### Chart.jsプラグインの活用

`chartjs-plugin-dragdata`を使用して、グラフ上の点をドラッグできるインタラクティブな機能を実装しました。

**ドラッグ制約:**
- 人手アノテーション（dataset 1）のみドラッグ可能
- スコアは0-9の範囲に自動制限
- ドラッグ終了時に状態を更新

### UIデザイン

モダンなダークテーマUIを維持しながら、グラフセクションを追加：
- 2x2グリッドレイアウトで4つのグラフを整然と配置
- 凡例で機械/人手アノテーションを明確に区別
- レスポンシブデザイン（モバイルで1カラムに）
- 視覚的なフィードバック（保存ボタンの状態変化）

## まとめ

グラフ表示と人手アノテーション機能を追加することで、well-scenarioシステムがより実用的になりました：

- **可視化**: メトリクススコアの推移を一目で把握できる
- **調整**: LLMの評価を人間が微調整できる
- **データ品質**: 機械と人間の評価を分離保存することで、両方の視点を保持

すべての機能が実装され、動作確認も完了しています。
