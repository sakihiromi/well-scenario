"""
metric_annotator.py
発言に対して各指標のスコアをアノテーションするモジュール
"""
import json
from typing import List, Dict, Any
from openai import OpenAI
import os


class MetricAnnotator:
    """発言に対して4つの指標でアノテーションを行うクラス"""
    
    def __init__(self, api_key: str, model_name: str, extra_json_path: str):
        """
        Args:
            api_key: OpenAI APIキー
            model_name: 使用するモデル名
            extra_json_path: 指標定義JSONのパス
        """
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.metrics_def = self._load_metrics(extra_json_path)
    
    def _load_metrics(self, path: str) -> Dict[str, Any]:
        """指標定義を読み込む"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_speaker(self, utt: Dict[str, Any]) -> str:
        """発言者名を取得（様々なキー名に対応）"""
        for key in ["speaker", "name", "発言者", "話者", "参加者"]:
            if key in utt:
                return str(utt[key])
        return ""
    
    def _get_text(self, utt: Dict[str, Any]) -> str:
        """発言内容を取得（様々なキー名に対応）"""
        for key in ["text", "content", "message", "発言", "発言内容", "内容", "セリフ"]:
            if key in utt:
                return str(utt[key])
        return ""
    
    def annotate_scenario(
        self,
        scenario: List[Dict[str, str]],
        meeting_purpose: str,
        meeting_format: str
    ) -> List[Dict[str, Any]]:
        """
        シナリオ全体にアノテーションを付与
        
        Args:
            scenario: 発言のリスト [{"speaker": "名前", "text": "発言内容"}, ...]
            meeting_purpose: 会議の目的
            meeting_format: 会議の形式
            
        Returns:
            アノテーション付き発言リスト
        """
        annotated = []
        context = []  # これまでの発言履歴
        
        for utt in scenario:
            # キー名の正規化（speakerとtextを取得）
            speaker = self._get_speaker(utt)
            text = self._get_text(utt)
            
            if not speaker or not text:
                print(f"警告: 発言のフォーマットが不正です。スキップします: {utt}")
                continue
            
            # 正規化された発言オブジェクト
            normalized_utt = {"speaker": speaker, "text": text}
            
            # 各発言に対してアノテーション
            annotation = self._annotate_utterance(
                utterance=normalized_utt,
                context=context,
                meeting_purpose=meeting_purpose,
                meeting_format=meeting_format
            )
            
            annotated.append({
                "speaker": speaker,
                "text": text,
                "metrics": annotation
            })
            
            # コンテキストに追加
            context.append(f"{speaker}: {text}")
        
        return annotated
    
    def _annotate_utterance(
        self,
        utterance: Dict[str, str],
        context: List[str],
        meeting_purpose: str,
        meeting_format: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        単一の発言にアノテーションを付与
        
        Returns:
            {"威圧度": {"score": 5, "reason": "..."}, ...}
        """
        # コンテキストを整形
        context_text = "\n".join(context[-5:]) if context else "（会議の冒頭）"
        
        # 指標定義を整形
        metrics_text = self._format_metrics_definition()
        
        # プロンプト作成
        prompt = f"""以下の会議における発言を、4つの指標で評価してください。

【会議の目的】
{meeting_purpose}

【会議の形式】
{meeting_format}

【これまでの発言（直近5件）】
{context_text}

【評価対象の発言】
{utterance['speaker']}: {utterance['text']}

【評価指標の定義】
{metrics_text}

【評価方法】
各指標について0-9の10段階でスコアを付けてください：
- 0-3: 低スコア（良好な状態）
- 4-6: 中スコア（普通）
- 7-9: 高スコア（問題あり）

各指標について、スコアとその理由を簡潔に説明してください。

【出力形式】
以下のJSON形式で出力してください：
{{
  "威圧度": {{
    "score": 数値,
    "reason": "評価理由"
  }},
  "逸脱度": {{
    "score": 数値,
    "reason": "評価理由"
  }},
  "発言無効度": {{
    "score": 数値,
    "reason": "評価理由"
  }},
  "偏り度": {{
    "score": 数値,
    "reason": "評価理由"
  }}
}}

JSONのみを出力し、説明文は不要です。"""

        # LLM呼び出し
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "あなたは会議の質を評価する専門家です。与えられた指標定義に基づいて、発言を客観的に評価します。必ずJSON形式で出力してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 評価の一貫性のため低めに設定
            response_format={"type": "json_object"}
        )
        
        # レスポンスをパース
        content = response.choices[0].message.content
        
        # contentがNoneの場合のエラーハンドリング
        if content is None:
            if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
                raise ValueError(f"LLMがリクエストを拒否しました: {response.choices[0].message.refusal}")
            raise ValueError("LLMからの応答が空でした。APIキーやモデル名を確認してください。")
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLMの応答をJSONとしてパースできませんでした: {e}\n応答内容: {content[:200]}")
        
        return result
    
    def _format_metrics_definition(self) -> str:
        """指標定義を文字列として整形"""
        formatted = []
        
        for metric_name, metric_def in self.metrics_def.items():
            text = f"\n【{metric_name}】\n"
            text += f"定義: {metric_def.get('定義', '')}\n"
            
            if 'スコア基準' in metric_def:
                criteria = metric_def['スコア基準']
                text += "スコア基準:\n"
                for level, desc in criteria.items():
                    text += f"  {level}: {desc}\n"
            
            if '質問' in metric_def:
                text += f"評価の観点: {metric_def['質問']}\n"
            
            formatted.append(text)
        
        return "\n".join(formatted)


if __name__ == "__main__":
    # テスト用
    from dotenv import load_dotenv
    load_dotenv()
    
    annotator = MetricAnnotator(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
        extra_json_path="data/extra.json"
    )
    
    # サンプル発言でテスト
    test_scenario = [
        {"speaker": "前田課長", "text": "結論は？"},
        {"speaker": "田中", "text": "あの、えっと、アンケート結果なんですけど、自動会議設定機能は不評で...削除を提案したいんですが..."},
        {"speaker": "前田課長", "text": "改善案は？そんなことも検討してないのか。"}
    ]
    
    annotated = annotator.annotate_scenario(
        scenario=test_scenario,
        meeting_purpose="自動会議設定機能の評価結果報告",
        meeting_format="進捗報告会議"
    )
    
    print(json.dumps(annotated, ensure_ascii=False, indent=2))
