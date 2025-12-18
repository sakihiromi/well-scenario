# Well-Scenario グラフ表示・人手アノテーション機能 実装計画

## 概要

well-scenarioシステムに、以下の機能を追加します：

1. **グラフ表示機能**: シナリオの各発言に付与されたメトリクススコアを折れ線グラフで可視化
2. **人手アノテーション機能**: グラフ上の点をドラッグして手動でスコアを調整
3. **データ分離保存**: 機械アノテーションと人手アノテーションを別々に保存

これにより、機械による評価を可視化し、ユーザーがインタラクティブに調整できるシステムを構築します。

## ユーザー確認が必要な項目

> [!IMPORTANT]
> **well-meetingのグラフ実装について**
>
> well-meetingプロジェクトへのアクセス権がないため、グラフ表示の詳細な実装方法を確認できません。以下の点について教えていただけますか？
> 
> 1. well-meetingではどのようなグラフライブラリを使用していますか？（Chart.js, D3.js, Plotly等）
> 2. グラフの表示形式はどのようなものですか？（折れ線グラフ、複数メトリクスの重ね表示等）
> 3. グラフの編集機能はどのように実装されていますか？
>
> これらの情報がない場合、以下の方針で進めます：
> - グラフライブラリ: **Chart.js**（軽量で使いやすい）
> - 表示形式: **4つのメトリクスそれぞれの折れ線グラフ**
> - 編集機能: **Chart.jsプラグイン + カスタムドラッグ実装**

> [!WARNING]
> **JSONスキーマの変更**
>
> 人手アノテーション機能の追加により、JSONファイルの構造が変更されます：
> - 既存: `scenario[].metrics[metric_name] = {score, reason}`
> - 新規: `scenario[].metrics[metric_name] = {machine_score, machine_reason, human_score?, human_reason?, edited_at?}`
>
> または：
> - `scenario[].machine_annotations` と `scenario[].human_annotations` を分離
>
> どちらの方式を希望されますか？（推奨: 後者の分離方式）

## 提案する変更内容

### データ構造の設計

#### [MODIFY] [JSONスキーマ](file:///Users/saki/lab/US/well-scenario/data/outputs)

現在のJSONファイル構造を拡張します：

```json
{
  "metadata": {
    "generated_at": "...",
    "meeting_purpose": "...",
    "meeting_format": "...",
    "num_utterances": 22,
    "profile_filename": "...",
    "model": "gpt-4o-mini",
    "sanitize_mode": false,
    "last_human_annotation": "2025-12-14T16:30:00.000Z"  // 新規追加
  },
  "scenario": [
    {
      "speaker": "田中",
      "text": "...",
      "machine_annotations": {  // 既存のmetricsをリネーム
        "威圧度": {
          "score": 2,
          "reason": "..."
        },
        "逸脱度": { "score": 1, "reason": "..." },
        "発言無効度": { "score": 1, "reason": "..." },
        "偏り度": { "score": 2, "reason": "..." }
      },
      "human_annotations": {  // 新規追加
        "威圧度": {
          "score": 3,
          "edited_at": "2025-12-14T16:30:00.000Z",
          "note": "ユーザーによる調整"
        }
        // 他のメトリクスは編集されていない場合は含まれない
      }
    }
  ]
}
```

---

### バックエンド (Flask API)

#### [MODIFY] [app.py](file:///Users/saki/lab/US/well-scenario/app.py)

新しいAPIエンドポイントを追加：

**1. 人手アノテーション保存API**

```python
@app.route('/api/output/<path:filename>/annotations', methods=['POST'])
def save_human_annotations(filename):
    """人手アノテーションを保存"""
    # リクエストデータ: { "annotations": { "0": {"威圧度": {"score": 3, "note": "..."}}, ... } }
    # ファイルを読み込み、human_annotationsセクションを更新
    # タイムスタンプを追加して保存
```

**2. 既存のget_output関数**

既存のままで問題なし（新しいスキーマに対応）

---

### フロントエンド (HTML/CSS/JavaScript)

#### [NEW] [static/chart_editor.js](file:///Users/saki/lab/US/well-scenario/static/chart_editor.js)

グラフ表示と編集機能を実装する新しいモジュール：

- **Chart.jsの統合**: CDNまたはnpmでインストール
- **グラフコンポーネント**: 
  - 4つのメトリクス別に折れ線グラフを作成
  - X軸: 発言番号（#1, #2, ...）
  - Y軸: スコア（0-9）
  - 機械アノテーション: 実線で表示
  - 人手アノテーション: 点線または異なる色で表示
- **ドラッグ機能**: 
  - Chart.jsプラグイン `chartjs-plugin-dragdata` を使用
  - または、カスタムイベントハンドラで実装
  - ドラッグ時にスコアの値を0-9に制限
- **状態管理**: 
  - 変更されたアノテーションをメモリに保持
  - 保存ボタンクリック時にAPIへ送信

#### [MODIFY] [templates/index.html](file:///Users/saki/lab/US/well-scenario/templates/index.html)

グラフ表示セクションを追加：

```html
<!-- シナリオ表示セクションの後に追加 -->
<section id="graph-section" class="graph-section" style="display: none;">
    <div class="graph-header">
        <h2>📈 メトリクススコアのグラフ</h2>
        <button id="save-annotations-btn" class="btn-secondary" disabled>
            💾 人手アノテーションを保存
        </button>
    </div>
    
    <div class="graph-container">
        <div class="graph-item">
            <h3>威圧度</h3>
            <canvas id="chart-intimidation"></canvas>
        </div>
        <div class="graph-item">
            <h3>逸脱度</h3>
            <canvas id="chart-deviation"></canvas>
        </div>
        <div class="graph-item">
            <h3>発言無効度</h3>
            <canvas id="chart-ineffectiveness"></canvas>
        </div>
        <div class="graph-item">
            <h3>偏り度</h3>
            <canvas id="chart-bias"></canvas>
        </div>
    </div>
    
    <div class="graph-legend">
        <span class="legend-item">
            <span class="legend-line machine"></span> 機械アノテーション
        </span>
        <span class="legend-item">
            <span class="legend-line human"></span> 人手アノテーション
        </span>
    </div>
</section>
```

#### [MODIFY] [static/script.js](file:///Users/saki/lab/US/well-scenario/static/script.js)

メイン機能に追加：

- シナリオロード時にグラフを初期化
- chart_editor.jsの関数を呼び出し
- 保存ボタンのイベントハンドラ

#### [MODIFY] [static/style.css](file:///Users/saki/lab/US/well-scenario/static/style.css)

グラフセクションのスタイリング：

- `.graph-section`: セクションレイアウト
- `.graph-container`: 2x2グリッドレイアウト（4つのグラフ）
- `.graph-item`: 各グラフのコンテナ
- `.graph-legend`: 凡例のスタイル
- レスポンシブ対応

---

### 依存関係の追加

#### [MODIFY] [requirements.txt](file:///Users/saki/lab/US/well-scenario/requirements.txt)

現在のままで問題なし（フロントエンドのみの変更のため）

#### [MODIFY] [templates/index.html](file:///Users/saki/lab/US/well-scenario/templates/index.html)

Chart.jsライブラリの追加：

```html
<head>
    ...
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-dragdata@2.2.5/dist/chartjs-plugin-dragdata.min.js"></script>
</head>
```

## 検証計画

### 自動テスト

1. **バックエンドAPI**
   ```bash
   # Flaskサーバーを起動
   python app.py
   
   # curlでAPIテスト
   curl -X POST http://localhost:5000/api/output/test.json/annotations \
     -H "Content-Type: application/json" \
     -d '{"annotations": {"0": {"威圧度": {"score": 5, "note": "test"}}}}'
   ```

2. **JSONスキーマ検証**
   - 既存のシナリオファイルを読み込み
   - 人手アノテーションを追加
   - スキーマの整合性を確認

### 手動検証

1. **グラフ表示**
   - ブラウザで `http://localhost:5000` にアクセス
   - シナリオを生成またはload
   - グラフが正しく表示されることを確認

2. **インタラクティブ編集**
   - グラフ上の点をドラッグ
   - スコアが0-9の範囲内で変更されることを確認
   - 変更された点が視覚的に区別できることを確認

3. **保存機能**
   - 複数の点を編集
   - 保存ボタンをクリック
   - JSONファイルに反映されることを確認
   - ページをリロードして変更が保持されることを確認

4. **UIの操作性**
   - レスポンシブデザインの確認
   - モバイル端末での動作確認（タッチ操作）
