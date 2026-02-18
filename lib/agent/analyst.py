# lib/agent/analyst.py
import geopandas as gpd

from pathlib import Path

from .base_agent import BaseAgent
from ..utils.propmpt_utils import PromptType, PromptLoader
from ..schema.report import ReportResponse, Report
from ..schema.geography import RegionSummaryResponse, RegionSummary
from ..core.project import Project

class AnalysisAgent(BaseAgent):
    def __init__(
            self, 
            text_generator, 
            project: Project, 
            region_summary: RegionSummary=None, 
            report: Report=None
        ):

        super().__init__(text_generator)
        self.project = project
        self.region_summary = region_summary
        self.report = report
    
    def analyze_current_issues(self, current_issues:str):
        analysis_path = self.project.results["analysis"]

        if not analysis_path.exists():
            # --- 生成モード ---
            # report = self._create_report(current_issues)
            report = self._thinking_about_report(current_issues)
            print(f"Analysis result generated and saved to: {analysis_path}")
        else:
            # --- ロードモード ---
            # BaseAgentの静的メソッド（または単なるjson.load）を使って復元
            analysis_data = self.load_json(analysis_path)
            report = Report(**analysis_data)
            print(f"Analysis result loaded from: {analysis_path}")
        
        self.report = report
        return report

    def analyze_region(self, spot_data: gpd.GeoDataFrame):
        analysis_path = self.project.results["geography"]

        if not analysis_path.exists():
            # AIに渡すための地域概要テキストの構築
            spot_list = ""
            for _, row in spot_data.iterrows():
                # 順番、名前、説明を1行にまとめる
                spot_list += f"name: {row['name']} / explanation: {row['explanation']}\n"

            # AIに分析を依頼
            # region_summary = self._create_region_summary(spot_list)
            region_summary = self._thinking_about_region(spot_list)
            print(f"Region analysis saved to: {analysis_path}")
        else:
            # ロードモード（既にある場合は再利用）
            data = self.load_json(analysis_path)
            # JSONから RegionSummary オブジェクトに復元
            region_summary = RegionSummary(**data)
            print(f"Region analysis loaded from: {analysis_path}")
        
        self.region_summary = region_summary
        return self.region_summary

    def _create_report(self, current_situation: dict) -> Report:
        # パスの解決
        prompt_path = PromptLoader.get_path(self.project.prompt_dir, PromptType.CREATE_REPORT)

        # 変数の組み立て
        variables = {
            "regional_summary": self.region_summary.summary,
            "regional_feature": self.region_summary.features,
            "known_issues": current_situation["known_issues"],
            "problems": current_situation["problmes"],
            "future_plan": current_situation["future_plan"]
        }
    
        # 実行（BaseAgentの_executeを呼び出し）
        response = self._execute(prompt_path, variables, ReportResponse)
        
        if response.status == "ready" and response.result:
            response.result.save_json(self.project.results["analysis"])
            return response.result
        else:
            # エラーメッセージを「分析レポート」に修正
            raise ValueError(f"AIからの分析レポート生成に失敗しました: {response.message}")
    
    def _create_region_summary(self, regional_info: str) -> RegionSummary:
        prompt_path = PromptLoader.get_path(self.project.prompt_dir, PromptType.CREATE_REGION_SUMMARY)

        variables = {
            "regional_info": regional_info,
        }
    
        # スキーマクラス名が RegionSummaryResponse 等であることを確認してください
        response = self._execute(prompt_path, variables, RegionSummaryResponse) 
        
        if response.status == "ready" and response.result:
            # response.result が RegionSummary オブジェクトであることを期待
            response.result.save_json(self.project.results["geography"])
            return response.result
        else:
            raise ValueError(f"AIからの分析レポート生成に失敗しました: {response.message}")
    
    def _thinking_about_region(self, regional_info: str) -> RegionSummary:
        self.region_summary = RegionSummary()
        
        # 2. 履歴の初期化
        conversation_history = [{
            "role": "system", 
            "content": f"あなたは地域活性化の専門アナリストです。以下の情報を読み込み、各項目を順に決定してください。\n\n"
            f"地域情報:\n{regional_info}\n\n"
        }]

        # --- ステップ1: タイトルの決定 ---
        conversation_history.append({
            "role": "user", 
            "content": "この地域を象徴する魅力的な『タイトル』を1つ提案してください。\n\n"
            "【制約条件】\n"
                "- 挨拶や前置きは不要。タイトルのみを出力すること。\n"
                "- タイトルは短く、印象的で、地域の特徴を端的に表現するものとしてください。\n"
        })
        self.region_summary.title = self._chat_step(conversation_history)
        conversation_history.append({"role": "assistant", "content": self.region_summary.title})
        print(f"DEBUG: Title determined -> {self.region_summary.title}")

        # --- ステップ2: 概要の決定 ---
        conversation_history.append({
            "role": "user", 
            "content": "次に、この地域の全体的な『概要』を客観的かつ詳細に整理してください。\n\n"
            "【制約条件】\n"
                "- 挨拶や前置きは不要。概要のみを出力すること。\n"
                "- 地域情報として提供された情報を網羅的に説明すること\n"
        })
        self.region_summary.summary = self._chat_step(conversation_history)
        conversation_history.append({"role": "assistant", "content": self.region_summary.summary})
        print(f"DEBUG: Summary determined -> {self.region_summary.summary}")

        # --- ステップ3: 特徴の決定 ---
        conversation_history.append({
            "role": "user", 
            "content": "最後に、自然、歴史、娯楽などの観点から、この地域の具体的な『特徴』を詳しく説明してください。\n\n"
            "【制約条件】\n"
                "- 挨拶や前置きは不要。特徴のみを出力すること。\n"
                "- それぞれの観点から、具体的な特徴を1つ以上記述すること。\n"
                "- 一般的な観光地としての観点から観光地としての魅力を高めることを意識して記述すること。"
        })
        self.region_summary.features = self._chat_step(conversation_history)
        conversation_history.append({"role": "assistant", "content": self.region_summary.features})
        print(f"DEBUG: Features determined -> {self.region_summary.features}")

        # 4. 全項目が埋まった状態で保存・返却
        self.region_summary.save_json(self.project.results["geography"])
        return self.region_summary
    
    def _thinking_about_report(self, current_situation: dict) -> Report:
        """
        情報を多角的に分析し、レポートの各項目を一つずつ思考しながら埋めていく。
        """
        self.report = Report()
        self.report.title = self.region_summary.title 

        print(current_situation.keys())
        
        conversation_history = [{
            "role": "system", 
            "content": (
                "あなたは戦略コンサルタント兼地域アナリストです。提供された情報を元に、論理的かつ創造的なレポートを作成してください。\n\n"
                "【制約条件】\n"
                "- 新しい現地体験型のラジオドラマ風の音声ガイドを開発すること前提に記述してください。"
            )
        }]

        # --- ステップ1: 調査背景 ---
        project_info = (
            f"【タイトル】: {self.region_summary.title}\n"
            f"【地域概要】: {self.region_summary.summary}\n"
            f"【地域特徴】: {self.region_summary.features}\n"
            f"【既知の課題】: {current_situation['known_issues']}\n"
            f"【現在の問題】: {current_situation['problems']}"
        )

        conversation_history.append({
            "role": "user", 
            "content": (
                f"以下の情報を元に、このプロジェクトの『調査背景（400字程度）』として記述してください。\n\n情報:\n{project_info} \n"
                "【制約条件】\n"
                "- 挨拶や前置きは不要。分析結果のみを出力すること。\n"
                "- 文体は「だ・である」調とすること。\n"
                "- 項目ごとに見出し（###）を立ててて記述せよ。"
            )
        })
        background = self._chat_step(conversation_history)
        self.report.background = background

        conversation_history.append({
            "role": "user", 
            "content": (
                "既知の課題と現在の問題を踏まえた上で、現在の観光客の行動や傾向を分析してください。\n\n"
                "【制約条件】\n"
                "- 挨拶や前置きは不要。分析結果のみを出力すること。\n"
                "- 文体は「だ・である」調とすること。\n"
                "- 項目ごとに見出し（###）を立ててて記述せよ。"
            )
        })
        tourist_data_summary = self._chat_step(conversation_history)
        self.report.tourist_data_summary = tourist_data_summary

        # --- ステップ2: ターゲット層に関する分析 ---
        future_plan = (
            f"【将来計画】: {current_situation['future_plan']}"
        )
        conversation_history.append({
            "role": "user", 
            "content": (
                "将来計画と隠せ世代の特徴を踏まえて、このプロジェクトの『ターゲット層に関する分析（400字程度）』として記述してください。\n\n"
                f"将来計画:\n{future_plan} \n\n"
                "世代特徴:\n"
                "- 子供世代: 歴史よりも自然に興味を持つ傾向がある。知識が乏しいため、歴史上の人物や歴史上の出来事は知らない可能性がある。\n"
                "- 若年世代: 歴史や文化に対する関心が薄い傾向がある。SNSなどで話題になっているスポットやアミューズメント性の高い体験を求める傾向がある。\n"
                "- 中年世代: 歴史的な町並みや落ち着いた雰囲気を好む傾向があり、一般的レベルの歴史や自然の知識を有している可能性がある。トリビア的な要素を好む傾向がある\n"
                "- 高齢世代: 歴史や文化に対する関心が高い傾向がある。地域の伝統や歴史的な背景を理解し、深く知ることを好む傾向がある。\n\n"
                "【制約条件】\n"
                "- 挨拶や前置きは不要。分析結果のみを出力すること。\n"
                "- 文体は「だ・である」調とすること。\n"
                "- 項目ごとに見出し（###）を立ててて記述せよ。\n"
            )
        })
        target_analysis = self._chat_step(conversation_history)
        self.report.target_layer = target_analysis
        conversation_history.append({"role": "assistant", "content": target_analysis})

        
        # --- ステップ3: 観光客データの要約と潜在ニーズ ---
        conversation_history.append({
            "role": "user", 
            "content": (
                "現状の問題点とターゲット層からそこから推測される『潜在的なニーズ』を分析してください。\n"
                "【制約条件】\n"
                "- 挨拶や前置きは不要。分析結果のみを出力すること。\n"
                "- 文体は「だ・である」調とすること。\n"
                "- 項目ごとに見出し（###）を立てて記述せよ。\n"
            )
        })
        thought_needs = self._chat_step(conversation_history)
        self.report.potential_needs = thought_needs # 思考プロセスをそのまま代入
        conversation_history.append({"role": "assistant", "content": thought_needs})

        # --- ステップ4: 潜在シーズとターゲット層 ---
        conversation_history.append({
            "role": "user", 
            "content": (
                "地域の将来計画や特徴を活かした音声ガイドのコンテンツ制作に向けて『潜在的なシーズ（可能性の種）』を具体的に特定してください。\n\n"
                "【制約条件】\n"
                "- 挨拶や前置きは不要。分析結果のみを出力すること。\n"
                "- 文体は「だ・である」調とすること。\n"
                "- 項目ごとに見出し（###）を立てて記述せよ。\n"
            )
        })
        thought_seeds = self._chat_step(conversation_history)
        self.report.potential_seeds = thought_seeds
        conversation_history.append({"role": "assistant", "content": thought_seeds})
        
        self.report.save_json(self.project.results["analysis"])
        return self.report