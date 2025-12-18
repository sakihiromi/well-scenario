"""
scenario_generator.py
会議シナリオを生成するモジュール
"""
import json
from typing import List, Dict, Any
from openai import OpenAI
import os


class ScenarioGenerator:
    """会議シナリオを自動生成するクラス"""
    
    def __init__(self, api_key: str, model_name: str, sanitize_mode: bool = True, extra_json_path: str = "data/extra.json"):
        """
        Args:
            api_key: OpenAI APIキー
            model_name: 使用するモデル名
            sanitize_mode: プロフィールの過激表現を緩和するかどうか（デフォルト: True）
            extra_json_path: 指標定義JSONのパス
        """
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.sanitize_mode = sanitize_mode
        self.extra_json_path = extra_json_path
        self.metric_definitions = self._load_metric_definitions()
    
    def load_profiles(self, profile_path: str) -> List[Dict[str, Any]]:
        """
        プロフィールJSONを読み込む
        
        Args:
            profile_path: プロフィールJSONのパス
            
        Returns:
            参加者プロフィールのリスト
        """
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_scenario(
        self,
        profiles: List[Dict[str, Any]],
        meeting_purpose: str,
        meeting_format: str,
        num_utterances: int = 40,
        focus_metrics: List[str] = None,
        target_ratio: int = 50
    ) -> List[Dict[str, str]]:
        """
        会議シナリオを生成する
        
        Args:
            profiles: 参加者プロフィールのリスト
            meeting_purpose: 会議の目的
            meeting_format: 会議の形式
            num_utterances: 生成する発言数
            focus_metrics: 重点を置く指標のリスト（例: ["威圧度", "逸脱度"]）
                          Noneまたは空の場合は全指標をバランスよく含める
            target_ratio: 重点指標の高スコア（7-9）発言の目標割合（10-90%）
                         focus_metricsが指定されている場合のみ有効
            
        Returns:
            発言のリスト [{"speaker": "名前", "text": "発言内容"}, ...]
        """
        # プロフィール情報を整形
        profile_text = self._format_profiles(profiles)
        
        # 重点指標の設定（Noneまたは空の場合は全指標）
        if not focus_metrics:
            focus_metrics = ["威圧度", "逸脱度", "発言無効度", "偏り度"]
        
        # 指標に関する詳細情報を生成
        metric_instructions = self._generate_metric_instructions(focus_metrics, num_utterances, target_ratio)
        
        # プロンプト作成  
        prompt = f"""【学術研究：会議コミュニケーション分析用データセット生成】

本タスクは、会議の質を評価するAIモデルのトレーニングデータ作成を目的とした学術研究です。
生成されたシナリオは、問題のあるコミュニケーションパターンを検出し、
職場環境の改善に資するための分析に使用されます。

以下の設定に基づいて、分析用の会議シナリオを生成してください。

---
■ 会議設定
- 目的: {meeting_purpose}
- 形式: {meeting_format}

■ 登場人物の行動特性
{profile_text}

**注意**: 各登場人物の性格や行動特性（話好き、雑談好き、脱線しやすいなど）を積極的に反映してください。

■ 評価指標の詳細
{metric_instructions}

■ 生成要件
1. **会議の構成**: 自然な会議の流れ（導入→議論→まとめ）

2. **登場人物の特性を最優先**:
   - 上記の登場人物の性格や行動特性を忠実に反映してください
   - プロフィールに「雑談好き」「脱線しやすい」とあれば、積極的に実行してください
   
3. **発言数**: 約{num_utterances}個の発言で構成

4. **自然な対話**:
   - 発言内に「」（カギカッコ）や引用符を使用しないでください
   - 会議の締めくくりは通常の挨拶（「お疲れ様でした」「ありがとうございました」）で問題ありません

■ 出力形式（JSON配列）
[
  {{"speaker": "発言者名", "text": "発言内容"}},
  ...
]
"""

        # LLM呼び出し - 指標に応じたシステムプロンプトを生成
        if focus_metrics and '逸脱度' in focus_metrics:
            if target_ratio >= 50:
                system_prompt = f"""あなたは会議シナリオ生成の専門家です。

**最重要指示**: 
- このシナリオでは、話が脱線しやすい会議を作成してください
- 登場人物の「雑談好き」「脱線しやすい」という性格を最大限に発揮させてください
- 会議の目的から**頻繁に**話題を逸らし、個人的な話題（趣味、週末、家族、食べ物、旅行など）を**積極的に**含めてください
- 全{num_utterances}発言のうち、約{int(num_utterances * target_ratio / 100)}発言は会議と無関係な雑談にしてください

**脱線のパターン例**:
- 会議の話題 → 個人的な経験談 → 趣味の話 → 完全に雑談
- 「〜といえば」「それで思い出したんですが」を多用
- 本題に戻そうとする発言は流される

**注意**: 会議の締めくくりの挨拶（「お疲れ様でした」「ありがとうございました」など）は通常の終了表現であり、脱線ではありません。

JSON形式で正確に出力してください。"""
            else:
                system_prompt = f"""あなたは会議シナリオ生成の専門家です。

**重要指示**:
- 基本的には正常な会議ですが、時々話が脱線します
- 全{num_utterances}発言のうち、約{int(num_utterances * target_ratio / 100)}発言だけ脱線させてください
- 脱線は自然な流れで発生させてください

JSON形式で正確に出力してください。"""
        else:
            system_prompt = """あなたは会議シナリオ生成の専門家です。

**重要な指示**:
- 登場人物の性格や行動特性を忠実に反映してください
- リアルで自然な会話を心がけてください

指定された設定に従って、自然な会議の会話を生成してください。
JSON形式で正確に出力してください。"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.95,  # 多様性を向上
            response_format={"type": "json_object"}
        )
        
        # レスポンスをパース
        content = response.choices[0].message.content
        
        # contentがNoneの場合のエラーハンドリング
        if content is None:
            # refusal messageをチェック
            if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
                raise ValueError(f"LLMがリクエストを拒否しました: {response.choices[0].message.refusal}")
            raise ValueError("LLMからの応答が空でした。APIキーやモデル名を確認してください。")
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLMの応答をJSONとしてパースできませんでした: {e}\n応答内容: {content[:200]}")
        
        # リスト形式に変換（キーが異なる場合の対応）
        scenario_list = []
        if isinstance(result, dict):
            # 様々なキー名に対応
            for key in ["scenario", "utterances", "dialogue", "conversation", "messages", "発言", "シナリオ"]:
                if key in result and isinstance(result[key], list):
                    scenario_list = result[key]
                    break
            
            if not scenario_list:
                # 最初のリスト値を返す
                for value in result.values():
                    if isinstance(value, list):
                        scenario_list = value
                        break
            
            # dictの中にリストが見つからない場合
            if not scenario_list:
                raise ValueError(f"JSON応答にシナリオのリストが見つかりませんでした。キー: {list(result.keys())}")
        elif isinstance(result, list):
            scenario_list = result
        
        # 各発言のキー名を正規化
        normalized = []
        for utt in scenario_list:
            if not isinstance(utt, dict):
                continue
            
            # speakerキーの正規化
            speaker = None
            for key in ["speaker", "name", "発言者", "話者", "参加者"]:
                if key in utt:
                    speaker = utt[key]
                    break
            
            # textキーの正規化
            text = None
            for key in ["text", "content", "message", "発言", "発言内容", "内容", "セリフ"]:
                if key in utt:
                    text = utt[key]
                    break
            
            if speaker and text:
                normalized.append({"speaker": speaker, "text": text})
        
        return normalized
    
    def _load_metric_definitions(self) -> Dict[str, Any]:
        """extra.jsonから指標定義を読み込む"""
        try:
            with open(self.extra_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告: {self.extra_json_path} が見つかりません。デフォルトの指標定義を使用します。")
            return {}
    
    def _generate_metric_instructions(self, focus_metrics: List[str], num_utterances: int, target_ratio: int) -> str:
        """重点指標の詳細説明を生成"""
        if not self.metric_definitions:
            return "※指標定義ファイルが読み込まれていません"
        
        # 重点指標が指定されていない場合
        if not focus_metrics or focus_metrics == ["威圧度", "逸脱度", "発言無効度", "偏り度"]:
            return """

## 評価指標のバランス

全ての指標（威圧度、逸脱度、発言無効度、偏り度）について、低スコア（1-3）、中スコア（4-6）、高スコア（7-9）の発言をバランスよく含めてください。
"""
        
        # 重点指標が指定されている場合
        instructions = ["\n\n## 重点指標の反映\n"]
        instructions.append(f"以下の指標について、**全発言の約{target_ratio}%**がスコア7-9になるよう意図的に調整してください：\n")
        
        for metric_name in focus_metrics:
            if metric_name in self.metric_definitions:
                metric_def = self.metric_definitions[metric_name]
                instructions.append(f"\n### {metric_name}")
                instructions.append(f"- **定義**: {metric_def.get('定義', 'N/A')}")
                instructions.append(f"- **高スコア基準（7-9）**: {metric_def.get('スコア基準', {}).get('高スコア（7-9）', 'N/A')}")
                instructions.append(f"- **目標**: 全発言の約{target_ratio}%が{metric_name}のスコア7-9になるようにする\n")
        
        # 具体的な指示を追加
        target_count = int(num_utterances * target_ratio / 100)
        
        instructions.append(f"\n## 目標スコア分布")
        instructions.append(f"全{num_utterances}発言のうち、**約{target_count}発言({target_ratio}%)が高スコア(7-9)**になることを目安にしてください。")
        instructions.append(f"ただし、登場人物の性格・行動特性を最優先し、厳密な数値にこだわる必要はありません。\n")
        
        # 割合に応じた行動指針
        instructions.append("## 登場人物の行動指針")
        
        if target_ratio >= 70:
            instructions.append(f"- 高い割合({target_ratio}%)のため:")
            instructions.append("  * 登場人物の問題行動の特性（雑談好き、脱線しやすいなど）を存分に発揮させてください")
            instructions.append("  * 会議全体を通して積極的に問題行動を起こしてください")
            
        elif target_ratio >= 50:
            instructions.append(f"- 中〜高の割合({target_ratio}%)のため:")
            instructions.append("  * 登場人物の特性を活発に反映させてください")
            instructions.append("  * 序盤は普通、中盤以降は特性を積極的に発揮してください")
            
        elif target_ratio >= 30:
            instructions.append(f"- 中程度の割合({target_ratio}%)のため:")
            instructions.append("  * 序盤は抑えめ、中盤以降に登場人物の特性を反映させてください")
            instructions.append("  * 問題行動と正常な発言がバランスよく混在させてください")
            
        else:  # 10-20%
            instructions.append(f"- 低い割合({target_ratio}%)のため:")
            instructions.append("  * 基本的には正常な会議にし、時々登場人物の特性が出る程度にしてください")
            instructions.append("  * 序盤は完全に正常、中〜後半に少しだけ特性を反映させてください")
        
        return "\n".join(instructions)
    
    def _sanitize_instructions(self, instructions: str) -> str:
        """指示文から過激な表現を緩和（コンテンツポリシー対策）"""
        replacements = {
            "高圧的": "直接的なコミュニケーションスタイル",
            "威圧的": "強いリーダーシップ",
            "詰める": "確認する",
            "追い込む": "明確化を求める",
            "責任追及": "状況確認",
            "丸投げ": "委任",
            "忖度": "配慮",
            "都合の悪い": "困難な",
            "せいにする": "について確認する",
            "委縮": "慎重",
            "しどろもどろ": "丁寧に説明",
            "苛立ち": "関心を持ち",
            "強い口調": "明確な言葉",
            "気が重い": "慎重に検討",
        }
        result = instructions
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result
    
    def _format_profiles(self, profiles: List[Dict[str, Any]]) -> str:
        """プロフィール情報を文字列として整形（学術研究用フォーマット）"""
        formatted = []
        for p in profiles:
            text = f"◆ キャラクター: {p['id']}\n"
            if 'profile' in p:
                prof = p['profile']
                text += f"  - 役職設定: {prof.get('role', '不明')}\n"
                text += f"  - 行動方針: {prof.get('stance', '不明')}\n"
                text += f"  - 積極性パラメータ: {prof.get('motivation', 0.5)}\n"
                text += f"  - 発言頻度パラメータ: {prof.get('talkativeness', 0.5)}\n"
            if 'instructions' in p:
                instructions = p['instructions']
                if self.sanitize_mode:
                    instructions = self._sanitize_instructions(instructions)
                text += f"  - 行動パターン設定: {instructions}\n"
            formatted.append(text)
        
        return "\n".join(formatted)


if __name__ == "__main__":
    # テスト用
    from dotenv import load_dotenv
    load_dotenv()
    
    generator = ScenarioGenerator(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
    )
    
    # サンプルプロフィールで生成テスト
    profiles = generator.load_profiles("data/profiles/トライアル_飲み会ズレ_圧をかけ飲み会転換.json")
    scenario = generator.generate_scenario(
        profiles=profiles,
        meeting_purpose="自動会議設定機能の評価結果の報告と改善案の検討",
        meeting_format="進捗報告会議",
        num_utterances=15
    )
    
    print(json.dumps(scenario, ensure_ascii=False, indent=2))
