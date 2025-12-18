"""
app.py
Well-Scenario システムのメインFlaskアプリケーション
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from pathlib import Path
from datetime import datetime

from scenario_generator import ScenarioGenerator
from metric_annotator import MetricAnnotator

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)
CORS(app)

# 設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# モデル設定（新しい分離設定を優先、フォールバックで旧設定を使用）
SCENARIO_MODEL = os.getenv("SCENARIO_MODEL_NAME") or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
ANNOTATION_MODEL = os.getenv("ANNOTATION_MODEL_NAME") or os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
EXTRA_JSON_PATH = os.getenv("EXTRA_JSON_PATH", "data/extra.json")
PROFILES_DIR = os.getenv("PROFILES_DIR", "data/profiles")
OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", "data/outputs")
# サニタイズモード: "true", "1", "yes" で有効、それ以外で無効
SANITIZE_MODE = os.getenv("SANITIZE_MODE", "true").lower() in ("true", "1", "yes")

# 出力ディレクトリの作成
Path(OUTPUTS_DIR).mkdir(parents=True, exist_ok=True)

# モジュール初期化
generator = ScenarioGenerator(OPENAI_API_KEY, SCENARIO_MODEL, sanitize_mode=SANITIZE_MODE)
annotator = MetricAnnotator(OPENAI_API_KEY, ANNOTATION_MODEL, EXTRA_JSON_PATH)


@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')


@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    """利用可能なプロフィールファイル一覧を取得"""
    profiles_path = Path(PROFILES_DIR)
    
    if not profiles_path.exists():
        return jsonify({"error": "プロフィールディレクトリが見つかりません"}), 404
    
    # JSONファイルを検索
    json_files = []
    for json_file in profiles_path.glob("*.json"):
        json_files.append({
            "name": json_file.name,
            "path": str(json_file)
        })
    
    return jsonify({"profiles": json_files})


@app.route('/api/profile/<path:filename>', methods=['GET'])
def get_profile_content(filename):
    """特定のプロフィールファイルの内容を取得"""
    profile_path = Path(PROFILES_DIR) / filename
    
    if not profile_path.exists():
        return jsonify({"error": "プロフィールファイルが見つかりません"}), 404
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        return jsonify({"profile": profile_data})
    except Exception as e:
        return jsonify({"error": f"プロフィールの読み込みに失敗しました: {str(e)}"}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """指標定義を取得"""
    try:
        with open(EXTRA_JSON_PATH, 'r', encoding='utf-8') as f:
            metrics_data = json.load(f)
        return jsonify({"metrics": metrics_data})
    except Exception as e:
        return jsonify({"error": f"指標定義の読み込みに失敗しました: {str(e)}"}), 500


@app.route('/api/generate-scenario', methods=['POST'])
def generate_scenario():
    """シナリオを生成してアノテーション"""
    try:
        data = request.json
        
        # パラメータ取得
        meeting_purpose = data.get('meeting_purpose', '')
        meeting_format = data.get('meeting_format', '')
        profile_filename = data.get('profile_filename', '')
        num_utterances = data.get('num_utterances', 20)
        
        if not meeting_purpose or not meeting_format:
            return jsonify({"error": "会議の目的と形式を入力してください"}), 400
        
        # プロフィール読み込み
        if profile_filename:
            profile_path = Path(PROFILES_DIR) / profile_filename
        else:
            return jsonify({"error": "プロフィールファイルを選択してください"}), 400
        
        if not profile_path.exists():
            return jsonify({"error": "プロフィールファイルが見つかりません"}), 404
        
        profiles = generator.load_profiles(str(profile_path))
        
        # シナリオ生成
        print(f"シナリオ生成中: 目的={meeting_purpose}, 形式={meeting_format}")
        scenario = generator.generate_scenario(
            profiles=profiles,
            meeting_purpose=meeting_purpose,
            meeting_format=meeting_format,
            num_utterances=num_utterances
        )
        
        if not scenario:
            return jsonify({"error": "シナリオの生成に失敗しました"}), 500
        
        # アノテーション付与
        print(f"アノテーション付与中: {len(scenario)}件の発言")
        annotated_scenario = annotator.annotate_scenario(
            scenario=scenario,
            meeting_purpose=meeting_purpose,
            meeting_format=meeting_format
        )
        
        # 結果をファイルに保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_base = Path(profile_filename).stem  # 拡張子を除いたファイル名
        output_filename = f"{timestamp}_{profile_base}.json"
        output_path = Path(OUTPUTS_DIR) / output_filename
        
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "meeting_purpose": meeting_purpose,
                "meeting_format": meeting_format,
                "num_utterances": len(annotated_scenario),
                "profile_filename": profile_filename,
                "scenario_model": SCENARIO_MODEL,
                "annotation_model": ANNOTATION_MODEL,
                "sanitize_mode": SANITIZE_MODE
            },
            "scenario": annotated_scenario
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"シナリオ保存完了: {output_path}")
        
        return jsonify({
            "success": True,
            "scenario": annotated_scenario,
            "metadata": {
                "meeting_purpose": meeting_purpose,
                "meeting_format": meeting_format,
                "num_utterances": len(annotated_scenario),
                "profile_filename": profile_filename,
                "saved_to": str(output_path)
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"エラーが発生しました: {str(e)}"}), 500


@app.route('/api/outputs', methods=['GET'])
def get_outputs():
    """保存済みシナリオ一覧を取得"""
    outputs_path = Path(OUTPUTS_DIR)
    
    if not outputs_path.exists():
        return jsonify({"outputs": []})
    
    outputs = []
    for json_file in sorted(outputs_path.glob("*.json"), reverse=True):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            outputs.append({
                "filename": json_file.name,
                "generated_at": data.get("metadata", {}).get("generated_at", ""),
                "meeting_purpose": data.get("metadata", {}).get("meeting_purpose", ""),
                "meeting_format": data.get("metadata", {}).get("meeting_format", ""),
                "num_utterances": data.get("metadata", {}).get("num_utterances", 0),
                "profile_filename": data.get("metadata", {}).get("profile_filename", "")
            })
        except Exception:
            continue
    
    return jsonify({"outputs": outputs})


@app.route('/api/output/<path:filename>', methods=['GET'])
def get_output(filename):
    """特定の保存済みシナリオを取得"""
    output_path = Path(OUTPUTS_DIR) / filename
    
    if not output_path.exists():
        return jsonify({"error": "ファイルが見つかりません"}), 404
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"ファイルの読み込みに失敗しました: {str(e)}"}), 500


@app.route('/api/output/<path:filename>/download', methods=['GET'])
def download_output(filename):
    """保存済みシナリオをダウンロード"""
    output_path = Path(OUTPUTS_DIR) / filename
    
    if not output_path.exists():
        return jsonify({"error": "ファイルが見つかりません"}), 404
    
    return send_file(
        output_path,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/output/<path:filename>/annotations', methods=['POST'])
def save_human_annotations(filename):
    """人手アノテーションを保存"""
    output_path = Path(OUTPUTS_DIR) / filename
    
    if not output_path.exists():
        return jsonify({"error": "ファイルが見つかりません"}), 404
    
    try:
        # リクエストデータを取得
        data = request.json
        annotations = data.get('annotations', {})
        
        # 既存のファイルを読み込み
        with open(output_path, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        # メタデータを更新
        file_data['metadata']['last_human_annotation'] = datetime.now().isoformat()
        
        # 各発言の人手アノテーションを更新
        for utterance_idx_str, metric_annotations in annotations.items():
            utterance_idx = int(utterance_idx_str)
            
            if utterance_idx < 0 or utterance_idx >= len(file_data['scenario']):
                continue
            
            utterance = file_data['scenario'][utterance_idx]
            
            # 初回の場合、metricsをmachine_annotationsにリネーム
            if 'metrics' in utterance and 'machine_annotations' not in utterance:
                utterance['machine_annotations'] = utterance.pop('metrics')
            
            # human_annotationsセクションを初期化
            if 'human_annotations' not in utterance:
                utterance['human_annotations'] = {}
            
            # 各メトリクスのアノテーションを更新
            for metric_name, metric_data in metric_annotations.items():
                utterance['human_annotations'][metric_name] = {
                    'score': metric_data.get('score'),
                    'edited_at': datetime.now().isoformat(),
                    'note': metric_data.get('note', '')
                }
        
        # ファイルに書き戻し
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "message": "人手アノテーションを保存しました",
            "saved_to": str(output_path)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"保存に失敗しました: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', 'localhost')
    
    print(f"Well-Scenario サーバー起動中...")
    print(f"URL: http://{host}:{port}")
    print(f"シナリオ生成モデル: {SCENARIO_MODEL}")
    print(f"アノテーションモデル: {ANNOTATION_MODEL}")
    print(f"サニタイズモード: {'有効' if SANITIZE_MODE else '無効'}")
    
    app.run(host=host, port=port, debug=True)
