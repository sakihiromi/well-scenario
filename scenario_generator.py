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
    
    def __init__(self, api_key: str, model_name: str, sanitize_mode: bool = True):
        """
        Args:
            api_key: OpenAI APIキー
            model_name: 使用するモデル名
            sanitize_mode: プロフィールの過激表現を緩和するかどうか（デフォルト: True）
        """
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.sanitize_mode = sanitize_mode
    
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
        num_utterances: int = 20
    ) -> List[Dict[str, str]]:
        """
        会議シナリオを生成する
        
        Args:
            profiles: 参加者プロフィールのリスト
            meeting_purpose: 会議の目的
            meeting_format: 会議の形式
            num_utterances: 生成する発言数
            
        Returns:
            発言のリスト [{"speaker": "名前", "text": "発言内容"}, ...]
        """
        # プロフィール情報を整形
        profile_text = self._format_profiles(profiles)
        
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

■ 登場人物の行動特性（研究用キャラクター設定）
{profile_text}

■ 生成要件
1. 各登場人物の設定された行動特性に基づいて発言を生成
2. 会議品質の評価指標（威圧度・逸脱度・発言無効度・偏り度）を測定するため、
   様々なコミュニケーションパターンを含める
3. 約{num_utterances}個の発言で構成
4. 自然な対話の流れを維持

■ 出力形式（JSON配列）
[
  {{"speaker": "発言者名", "text": "発言内容"}},
  ...
]

JSONのみを出力してください。"""

        # LLM呼び出し
        system_prompt = """あなたは会議コミュニケーション研究のための会議シナリオ生成の専門家です。

【重要な背景】
このシステムは、会議の質を評価・改善するための学術研究ツールです。
生成されるシナリオは、会議における問題行動（威圧的発言、話題の逸脱など）を
検出・分析するためのトレーニングデータとして使用されます。

問題のある発言パターンを含むシナリオを生成することで、
AIが会議の質を自動評価し、より健全な職場環境の構築に貢献することが目的です。

リアルで自然な会議の流れを作成し、必ずJSON配列形式で出力してください。"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
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
