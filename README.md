# 🎯 Well-Scenario

会議シナリオ生成＆指標アノテーションシステム

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange)](https://openai.com/)

---

## 📖 概要

Well-Scenarioは、参加者プロフィールと会議設定に基づいて、リアルな会議シナリオを自動生成し、各発言に対して4つの指標（威圧度、逸脱度、発言無効度、偏り度）でアノテーションを付与するシステムです。

会議の質を定量的に評価するための研究・評価用途で開発されています。

### ✨ 主な機能

| 機能 | 説明 |
|------|------|
| 📝 **シナリオ生成** | 参加者プロフィールに基づいてリアルな会議の流れを自動生成 |
| 📊 **指標アノテーション** | 各発言を4つの指標で0-9の10段階評価 |
| � **グラフ表示** | メトリクススコアを折れ線グラフで可視化 |
| ✏️ **人手アノテーション** | グラフ上で点をドラッグしてスコアを手動調整 |
| �👥 **プロフィール管理** | 既存のJSONファイルから参加者情報を読み込み |
| 🎨 **視覚的表示** | スコアに応じた色分けと詳細な理由説明 |
| 🌐 **Webインターフェース** | モダンなダークテーマUIで直感的に操作可能 |
| 💾 **自動保存** | 生成したシナリオをJSONファイルとして自動保存 |
| 🔧 **サニタイズモード** | プロフィールの過激表現を自動緩和（APIポリシー対策） |

---

## 🏗️ システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                        ブラウザ (Frontend)                       │
│                    index.html + script.js + style.css            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Flask Server (app.py)                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  /api/profiles │    │ /api/metrics │    │ /api/generate │      │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
        ┌─────────────────────┐   ┌─────────────────────┐
        │  ScenarioGenerator  │   │   MetricAnnotator   │
        │ (scenario_generator │   │ (metric_annotator   │
        │        .py)         │   │        .py)         │
        └─────────────────────┘   └─────────────────────┘
                    │                       │
                    │    OpenAI API         │
                    └───────────┬───────────┘
                                ▼
                    ┌─────────────────────┐
                    │   GPT-4o / GPT-4o   │
                    │     mini 等         │
                    └─────────────────────┘
```

### 処理フロー

1. **ユーザー入力**: 会議の目的、形式、参加者プロフィール、発言数を入力
2. **シナリオ生成**: `ScenarioGenerator`がLLMを使用してリアルな会議の流れを生成
3. **アノテーション**: `MetricAnnotator`が各発言を4つの指標で評価
4. **結果表示**: フロントエンドでスコアに応じた色分けと詳細表示

---

## 📊 評価指標

各発言は以下の4つの指標で0-9の10段階評価されます。

### 1. 威圧度

> 発言の威圧性や心理的圧力を評価

- **理論的背景**: Weblerの公正性理論、Leventhalの手続き的公正の公準
- **目的**: 威圧的な発言をやめさせ、安心して意見を言える場を維持

| スコア | 状態 | 説明 |
|:------:|:----:|------|
| 0-3 | 🟢 良好 | 相手を尊重し、建設的な批判や指摘を行う発言 |
| 4-6 | 🟡 普通 | 中立的だが建設性が限定的 |
| 7-9 | 🔴 問題あり | 過度な要求や相手を追い込む発言、皮肉、暗黙の圧力 |

### 2. 逸脱度

> 会議の目的からの逸脱度を評価

- **理論的背景**: Steenbergenらの討論の質評価指標
- **目的**: 会議を目的に沿った議論へと戻すこと

| スコア | 状態 | 説明 |
|:------:|:----:|------|
| 0-3 | 🟢 良好 | 会議の目的に直接関連し、議論を前進させる発言 |
| 4-6 | 🟡 普通 | 部分的に関連する発言や、目的からやや離れた発言 |
| 7-9 | 🔴 問題あり | 目的と無関係な発言、堂々巡り、進行を妨げる発言 |

### 3. 発言無効度

> 目的達成への貢献度（逆指標）を評価

- **理論的背景**: Weblerの実行性理論、エンパワーメント理論
- **目的**: 目的に合った重要な発言が見過ごされないよう再検討を促す

| スコア | 状態 | 説明 |
|:------:|:----:|------|
| 0-3 | 🟢 良好 | 目的達成に明確に寄与し、理解や共通理解の形成に貢献 |
| 4-6 | 🟡 普通 | 部分的には寄与するが、結びつきが不十分 |
| 7-9 | 🔴 問題あり | 目的達成にほとんど寄与せず、会議を停滞させる |

### 4. 偏り度

> 発言の公平性や偏りを評価

- **理論的背景**: Habermasの討議理論、Leventhalの手続き的公正の公準（偏り抑制）
- **目的**: 私利私欲や不公平な発言をやめさせること

| スコア | 状態 | 説明 |
|:------:|:----:|------|
| 0-3 | 🟢 良好 | 全員が平等に発言でき、公正性が保たれている |
| 4-6 | 🟡 普通 | 一部に偏りがあるが、公正性は部分的に保たれている |
| 7-9 | 🔴 問題あり | 特定の意見や参加者が議論を支配している |

---

## 🚀 セットアップ

### 必要要件

- Python 3.10以上
- OpenAI APIキー

### 1. 依存パッケージのインストール

```bash
cd /Users/saki/lab/US/well-scenario
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルを作成または編集してください：

```bash
# OpenAI API Settings
OPENAI_API_KEY=your-api-key-here

# Model Settings (モデル設定を分離)
SCENARIO_MODEL_NAME=gpt-4o-mini      # シナリオ生成用（制限が緩いモデル）
ANNOTATION_MODEL_NAME=gpt-4o         # アノテーション用（最新・高精度モデル）

# Server Settings
FLASK_PORT=5000
FLASK_HOST=localhost

# Paths
EXTRA_JSON_PATH=data/extra.json
PROFILES_DIR=data/profiles
OUTPUTS_DIR=data/outputs

# Sanitize Mode（プロフィールの過激表現を緩和）
SANITIZE_MODE=true
```

#### 環境変数の説明

| 変数名 | 必須 | デフォルト値 | 説明 |
|--------|:----:|--------------|------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI APIキー |
| `SCENARIO_MODEL_NAME` | ❌ | `gpt-4o-mini` | シナリオ生成に使用するモデル名 |
| `ANNOTATION_MODEL_NAME` | ❌ | `gpt-4o` | メトリクスアノテーションに使用するモデル名 |
| `OPENAI_MODEL_NAME` | ❌ | `gpt-4o` | 旧設定（後方互換性のため保持） |
| `FLASK_PORT` | ❌ | `5000` | サーバーのポート番号 |
| `FLASK_HOST` | ❌ | `localhost` | サーバーのホスト名 |
| `EXTRA_JSON_PATH` | ❌ | `data/extra.json` | 指標定義JSONのパス |
| `PROFILES_DIR` | ❌ | `data/profiles` | プロフィールディレクトリのパス |
| `OUTPUTS_DIR` | ❌ | `data/outputs` | シナリオ出力ディレクトリのパス |
| `SANITIZE_MODE` | ❌ | `true` | プロフィールの過激表現を緩和するか |

#### サニタイズモードについて

`SANITIZE_MODE=true` の場合、プロフィールの指示文から以下のような表現が自動的に緩和されます：

| 元の表現 | 緩和後 |
|---------|--------|
| 高圧的 | 直接的なコミュニケーションスタイル |
| 威圧的 | 強いリーダーシップ |
| 詰める | 確認する |
| 丸投げ | 委任 |
| 忖度 | 配慮 |

これはOpenAI APIのコンテンツポリシー対策として機能します。
研究目的で元のプロフィールをそのまま使用したい場合は `SANITIZE_MODE=false` に設定してください。

### 3. サーバーの起動

```bash
python app.py
```

サーバーが起動したら、ブラウザで以下にアクセス：
```
http://localhost:5000
```

---

## 📁 ファイル構成

```
well-scenario/
├── app.py                    # メインFlaskアプリケーション
├── scenario_generator.py     # シナリオ生成モジュール
├── metric_annotator.py       # 指標アノテーションモジュール
├── requirements.txt          # 依存パッケージ
├── .env                      # 環境変数設定
├── README.md                 # このファイル
├── data/
│   ├── extra.json            # 指標定義JSON
│   ├── profiles/             # 参加者プロフィールディレクトリ
│   │   ├── トライアル_飲み会ズレ.json
│   │   └── ...
│   └── outputs/              # 生成されたシナリオの保存先
│       └── 20241210_172130_トライアル_飲み会ズレ.json
├── templates/
│   └── index.html            # Webインターフェース
└── static/
    ├── style.css             # スタイルシート
    ├── script.js             # メインフロントエンドスクリプト
    └── chart_editor.js       # グラフ表示・編集スクリプト
```

---

## 🔧 モジュール詳細

### app.py - メインアプリケーション

Flaskベースのウェブサーバー。APIエンドポイントを提供し、フロントエンドとバックエンドを接続します。

**主な責務:**
- HTTPリクエストのルーティング
- 各モジュールの初期化と連携
- エラーハンドリング

### scenario_generator.py - シナリオ生成モジュール

`ScenarioGenerator` クラスが会議シナリオの自動生成を担当します。

**主な機能:**
- プロフィールJSONの読み込み
- LLMへのプロンプト構築
- シナリオ（発言リスト）の生成

```python
# 使用例
generator = ScenarioGenerator(api_key, model_name)
profiles = generator.load_profiles("profiles.json")
scenario = generator.generate_scenario(
    profiles=profiles,
    meeting_purpose="自動会議設定機能の評価結果報告",
    meeting_format="進捗報告会議",
    num_utterances=20
)
```

**生成パラメータ:**
- `temperature=0.8`: 多様性のある自然な発言を生成

### metric_annotator.py - 指標アノテーションモジュール

`MetricAnnotator` クラスが各発言の指標評価を担当します。

**主な機能:**
- 指標定義JSONの読み込み
- 発言ごとのコンテキストを考慮した評価
- 4つの指標のスコアと理由の生成

```python
# 使用例
annotator = MetricAnnotator(api_key, model_name, "extra.json")
annotated_scenario = annotator.annotate_scenario(
    scenario=scenario,
    meeting_purpose="自動会議設定機能の評価結果報告",
    meeting_format="進捗報告会議"
)
```

**評価パラメータ:**
- `temperature=0.3`: 評価の一貫性のため低めに設定
- コンテキスト: 直近5件の発言を考慮

---

## 📝 データフォーマット

### プロフィールJSON

参加者の情報を定義するJSONファイルです。

```json
[
  {
    "id": "前田課長",
    "instructions": "あなたは前田課長（男性）。高圧的だが雑談好き。飲み会が大好きで...",
    "voice": "ash",
    "profile": {
      "role": "課長",
      "stance": "トップの視点・対外調整重視",
      "motivation": 0.3,
      "talkativeness": 0.5
    }
  }
]
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|:----:|------|
| `id` | string | ✅ | 参加者名（発言者名として使用） |
| `instructions` | string | ✅ | 性格や行動指示（LLMへのプロンプトに使用） |
| `voice` | string | ❌ | 音声ID（他システム連携用） |
| `profile.role` | string | ❌ | 役職 |
| `profile.stance` | string | ❌ | 方針・立場 |
| `profile.motivation` | float | ❌ | やる気（0.0〜1.0） |
| `profile.talkativeness` | float | ❌ | 話好き度（0.0〜1.0） |

### 指標定義JSON (extra.json)

評価指標の定義を格納するJSONファイルです。

```json
{
  "威圧度": {
    "定義": "発言の威圧性を10段階で評価する...",
    "スコア基準": {
      "低スコア（0-3）": "相手を尊重し、建設的な批判や指摘を行う発言...",
      "中スコア（3-7）": "中立的な発言で威圧感はないが...",
      "高スコア（7-9）": "過度な要求や相手を追い込む発言..."
    },
    "質問": "この発言は相手にプレッシャーや恐怖を与えていないか？..."
  }
}
```

---

## 🌐 API エンドポイント

### `GET /api/profiles`

利用可能なプロフィールファイル一覧を取得

**レスポンス例:**
```json
{
  "profiles": [
    {"name": "トライアル_飲み会ズレ.json", "path": "..."},
    {"name": "トライアル_飲み会ズレ_圧をかけ飲み会転換.json", "path": "..."}
  ]
}
```

### `GET /api/profile/<filename>`

特定のプロフィールファイルの内容を取得

**パラメータ:**
- `filename`: プロフィールのファイル名

**レスポンス例:**
```json
{
  "profile": [
    {"id": "前田課長", "instructions": "...", "profile": {...}}
  ]
}
```

### `GET /api/metrics`

指標定義を取得

**レスポンス例:**
```json
{
  "metrics": {
    "威圧度": {"定義": "...", "スコア基準": {...}},
    "逸脱度": {...},
    "発言無効度": {...},
    "偏り度": {...}
  }
}
```

### `POST /api/generate-scenario`

シナリオを生成してアノテーション

**リクエストボディ:**
```json
{
  "meeting_purpose": "会議の目的",
  "meeting_format": "会議の形式",
  "profile_filename": "プロフィールファイル名",
  "num_utterances": 20
}
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|:----:|---------|------|
| `meeting_purpose` | string | ✅ | - | 会議の目的 |
| `meeting_format` | string | ✅ | - | 会議の形式 |
| `profile_filename` | string | ✅ | - | プロフィールファイル名 |
| `num_utterances` | int | ❌ | 20 | 発言数（5-50） |

**レスポンス例:**
```json
{
  "success": true,
  "scenario": [
    {
      "speaker": "前田課長",
      "text": "結論は？",
      "metrics": {
        "威圧度": {"score": 7, "reason": "短い言葉で相手を追い込む発言"},
        "逸脱度": {"score": 2, "reason": "会議の目的に沿った質問"},
        "発言無効度": {"score": 3, "reason": "議論を促進する発言"},
        "偏り度": {"score": 4, "reason": "特定の人物への質問だが不公平ではない"}
      }
    }
  ],
  "metadata": {
    "meeting_purpose": "自動会議設定機能の評価結果報告",
    "meeting_format": "進捗報告会議",
    "num_utterances": 20,
    "profile_filename": "トライアル_飲み会ズレ.json",
    "saved_to": "data/outputs/20241210_172130_トライアル_飲み会ズレ.json"
  }
}
```

### `GET /api/outputs`

保存済みシナリオ一覧を取得

**レスポンス例:**
```json
{
  "outputs": [
    {
      "filename": "20241210_172130_トライアル_飲み会ズレ.json",
      "generated_at": "2024-12-10T17:21:30.123456",
      "meeting_purpose": "自動会議設定機能の評価結果報告",
      "meeting_format": "進捗報告会議",
      "num_utterances": 20,
      "profile_filename": "トライアル_飲み会ズレ.json"
    }
  ]
}
```

### `GET /api/output/<filename>`

特定の保存済みシナリオを取得

**パラメータ:**
- `filename`: 出力ファイル名

**レスポンス例:**
```json
{
  "metadata": {
    "generated_at": "2024-12-10T17:21:30.123456",
    "meeting_purpose": "自動会議設定機能の評価結果報告",
    "meeting_format": "進捗報告会議",
    "num_utterances": 20,
    "profile_filename": "トライアル_飲み会ズレ.json",
    "model": "gpt-4o-mini",
    "sanitize_mode": false
  },
  "scenario": [...]
}
```

### `GET /api/output/<filename>/download`

保存済みシナリオをダウンロード

**パラメータ:**
- `filename`: 出力ファイル名

**レスポンス:**
- JSONファイルのダウンロード

### `POST /api/output/<filename>/annotations`

人手アノテーションを保存

**パラメータ:**
- `filename`: 出力ファイル名

**リクエストボディ:**
```json
{
  "annotations": {
    "0": {
      "威圧度": {
        "score": 5,
        "note": "ユーザーによる調整"
      }
    },
    "3": {
      "逸脱度": {
        "score": 7,
        "note": ""
      },
      "偏り度": {
        "score": 4,
        "note": "偏りを軽減"
      }
    }
  }
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "人手アノテーションを保存しました",
  "saved_to": "data/outputs/20241210_172130_トライアル_飲み会ズレ.json"
}
```

---

## 💾 出力ファイル形式

生成されたシナリオは自動的に `data/outputs/` ディレクトリに保存されます。

### ファイル名規則

```
{タイムスタンプ}_{プロフィール名}.json
例: 20241210_172130_トライアル_飲み会ズレ.json
```

### 出力JSONフォーマット

```json
{
  "metadata": {
    "generated_at": "2024-12-10T17:21:30.123456",
    "meeting_purpose": "自動会議設定機能の評価結果報告と改善案の検討",
    "meeting_format": "定例・進捗",
    "num_utterances": 20,
    "profile_filename": "トライアル_飲み会ズレ.json",
    "scenario_model": "gpt-4o-mini",
    "annotation_model": "gpt-4o",
    "sanitize_mode": false,
    "last_human_annotation": "2024-12-14T16:30:00.000000"
  },
  "scenario": [
    {
      "speaker": "前田課長",
      "text": "結論は？",
      "machine_annotations": {
        "威圧度": {"score": 7, "reason": "短い言葉で相手を追い込む発言"},
        "逸脱度": {"score": 2, "reason": "会議の目的に沿った質問"},
        "発言無効度": {"score": 3, "reason": "議論を促進する発言"},
        "偏り度": {"score": 4, "reason": "特定の人物への質問だが不公平ではない"}
      },
      "human_annotations": {
        "威圧度": {
          "score": 5,
          "edited_at": "2024-12-14T16:30:00.000000",
          "note": "ユーザーによる調整"
        }
      }
    },
    ...
  ]
}
```

### データフィールドの説明

#### メタデータ

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `generated_at` | string | シナリオ生成日時（ISO 8601形式） |
| `meeting_purpose` | string | 会議の目的 |
| `meeting_format` | string | 会議の形式 |
| `num_utterances` | int | 発言数 |
| `profile_filename` | string | 使用したプロフィールファイル名 |
| `scenario_model` | string | シナリオ生成に使用したLLMモデル |
| `annotation_model` | string | アノテーションに使用したLLMモデル |
| `sanitize_mode` | boolean | サニタイズモードの有効/無効 |
| `last_human_annotation` | string | 最後に人手アノテーションを保存した日時 |

#### シナリオ配列

各発言オブジェクトには以下のフィールドがあります：

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|:----:|------|
| `speaker` | string | ✅ | 発言者名 |
| `text` | string | ✅ | 発言内容 |
| `machine_annotations` | object | ✅ | LLMによる自動評価 |
| `human_annotations` | object | ❌ | ユーザーによる手動調整（編集された場合のみ） |

**machine_annotations / human_annotationsの構造:**

```json
{
  "威圧度": {
    "score": 7,
    "reason": "評価の理由",  // machine_annotationsのみ
    "edited_at": "2024-12-14T16:30:00.000000",  // human_annotationsのみ
    "note": "注釈"  // human_annotationsのみ
  }
}
```

---

## 🖥️ フロントエンド機能

### Webインターフェース

モダンなダークテーマUIを採用し、直感的に操作できます。

**入力セクション:**
- 会議の目的（テキスト入力）
- 会議の形式（セレクトボックス）
  - 定例・進捗
  - ブレインストーミング
  - 意思決定会議
  - 報告会
  - 打ち合わせ
  - その他
- 参加者プロフィール（セレクトボックス）
- 発言数（数値入力: 5-50）

**結果表示:**
- 参加者プロフィールのカード表示
- 発言ごとのスコア表示
  - 🟢 緑: 低スコア（0-3）- 良好
  - 🟡 黄: 中スコア（4-6）- 普通
  - 🔴 赤: 高スコア（7-9）- 問題あり
- 各スコアの評価理由

**グラフ表示・人手アノテーション:**
- 4つのメトリクス別の折れ線グラフ
  - 威圧度、逸脱度、発言無効度、偏り度
  - 青い実線: 機械アノテーション（LLMによる自動評価）
  - 赤い点線: 人手アノテーション（ユーザーによる調整）
- インタラクティブな編集機能
  - グラフ上の点をドラッグしてスコアを調整
  - スコアは0-9の範囲内に自動制限
  - 編集内容はリアルタイムで反映
- 保存機能
  - 編集したスコアを保存ボタンでJSON保存
  - 機械アノテーションと人手アノテーションを分離保存
  - 編集日時と注釈を記録

---

## 🛠️ 開発者向けガイド

### ローカル開発

```bash
# 開発サーバーの起動（デバッグモード有効）
python app.py
```

### モジュール単体テスト

```bash
# シナリオ生成のテスト
python scenario_generator.py

# アノテーションのテスト
python metric_annotator.py
```

### カスタマイズ

#### 新しい指標を追加する場合

1. `data/extra.json` に新しい指標を追加
2. `metric_annotator.py` のプロンプトを更新
3. `templates/index.html` の表示部分を更新

#### 新しい会議形式を追加する場合

`templates/index.html` のセレクトボックスを編集:

```html
<select id="meeting-format">
    <option value="新しい形式">新しい形式</option>
    ...
</select>
```

---

## ⚠️ 注意事項

- OpenAI APIキーが必要です
- 生成には数十秒かかる場合があります（発言数に依存）
- APIコストに注意してください（1回の生成で複数回のLLM呼び出しが発生）
- プロフィールJSONと指標定義JSONへのパスが正しく設定されていることを確認してください

---

## 🔍 トラブルシューティング

### プロフィールが読み込めない

```
❌ エラー: プロフィールディレクトリが見つかりません
```

**対処法:**
- `.env`ファイルの`PROFILES_DIR`パスが正しいか確認
- ディレクトリが存在するか確認
- JSONファイルが存在するか確認

### シナリオ生成に失敗する

```
❌ エラー: シナリオの生成に失敗しました
```

**対処法:**
- OpenAI APIキーが正しく設定されているか確認
- インターネット接続を確認
- コンソールでエラーログを確認
- APIクォータ/制限を確認

### LLMがリクエストを拒否する

```
❌ エラー: LLMがリクエストを拒否しました: I'm sorry, I can't assist with that request.
```

**対処法:**
- `SANITIZE_MODE=true` に設定してプロフィールの過激表現を緩和
- より穏やかなプロフィールファイルを使用
- `gpt-4o-mini` など制限の緩いモデルに変更

```bash
# .env で設定
SANITIZE_MODE=true
OPENAI_MODEL_NAME=gpt-4o-mini
```

### 指標アノテーションが表示されない

```
❌ エラー: 指標定義の読み込みに失敗しました
```

**対処法:**
- `.env`ファイルの`EXTRA_JSON_PATH`が正しいか確認
- `extra.json`ファイルが存在するか確認
- JSONの構文エラーがないか確認

### CORSエラー

**対処法:**
- Flask-CORSが正しくインストールされているか確認
- ブラウザのキャッシュをクリア

---

## 📦 依存パッケージ

| パッケージ | バージョン | 用途 |
|-----------|---------|------|
| flask | 3.0.0 | Webフレームワーク |
| flask-cors | 4.0.0 | CORS対応 |
| openai | 1.54.0 | OpenAI API クライアント |
| python-dotenv | 1.0.0 | 環境変数管理 |
| pandas | 2.1.4 | データ処理（拡張用） |

---

## 🔬 理論的背景

本システムの評価指標は以下の理論に基づいています：

- **Webler (1995)**: 公正性理論・実行性理論
- **Leventhal (1980)**: 手続き的公正の6つの公準
- **Habermas (1981)**: 討議理論
- **Steenbergen et al. (2003)**: 討論の質評価指標 (DQI)
- **エンパワーメント理論**: 有能感・連帯感・有効感

---

## 📄 ライセンス

このプロジェクトは研究・評価用途で開発されています。

---

## 📮 お問い合わせ

バグ報告や機能要望がある場合は、Issueを作成してください。
