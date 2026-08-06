# lib/agent/analyst.py
import geopandas as gpd

from .base_agent import BaseAgent
from ..core.project import Project
from ..schema import (
    Report,
    RegionSummary,
)

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
            report = self._create_report_sequential(current_issues)
            print(f"Analysis result generated and saved to: {analysis_path}")
        else:
            # --- ロードモード ---
            analysis_data = self.load_json(analysis_path)
            report = Report(**analysis_data)
            print(f"Analysis result loaded from: {analysis_path}")
        
        self.report = report
        return self.report

    def analyze_region(self, spot_data: gpd.GeoDataFrame):
        analysis_path = self.project.results["geography"]

        if not analysis_path.exists():
            # AIに渡すための地域概要テキストの構築
            spot_list = ""
            for _, row in spot_data.iterrows():
                # 順番、名前、説明を1行にまとめる
                spot_list += f"name: {row['name']} / explanation: {row['explanation']}\n"

            # AIに分析を依頼
            region_summary = self._create_region_summary_sequential(spot_list)
            print(f"Region analysis saved to: {analysis_path}")
        else:
            # ロードモード（既にある場合は再利用）
            data = self.load_json(analysis_path)
            region_summary = RegionSummary(**data)
            print(f"Region analysis loaded from: {analysis_path}")
        
        self.region_summary = region_summary
        return self.region_summary

    def _create_region_summary_sequential(self, regional_info: str) -> RegionSummary:
        self.region_summary = RegionSummary(title="", summary="", features="")

        # 2. 履歴の初期化
        conversation_history = [{
            "role": "system", 
            "content": f"あなたは地域活性化の専門アナリストです。以下の情報を読み込み、各項目を順に決定してください。\n\n"
            f"地域情報:\n{regional_info}\n\n"
        }]

        self.region_summary.title = self._ask_title(
            conversation_history,
            "この地域を象徴する魅力的な『タイトル』を1つ提案してください。タイトルは短く、"
            "印象的で、地域の特徴を端的に表現するものとしてください。",
        )

        self.region_summary.summary = self._ask_sequential(
            conversation_history,
            "次に、この地域の全体的な『概要』を客観的かつ詳細に整理してください。"
            "地域情報として提供された情報を網羅的に説明してください。\n\n"
            "【制約条件】\n- 挨拶や前置きは不要。概要のみを出力すること。",
        )

        self.region_summary.features = self._ask_sequential(
            conversation_history,
            "最後に、自然、歴史、娯楽などの観点から、この地域の具体的な『特徴』を詳しく"
            "説明してください。それぞれの観点から、具体的な特徴を1つ以上記述し、観光地としての"
            "魅力を高めることを意識してください。\n\n"
            "【制約条件】\n"
            "- 挨拶や前置きは不要。特徴のみを出力すること。\n"
            "- 箇条書き（リスト形式）ではなく、必ず一続きの文章として記述すること。",
        )

        # 4. 全項目が埋まった状態で保存・返却
        self.region_summary.save_json(self.project.results["geography"])
        return self.region_summary
    
    def _create_report_sequential(self, current_situation: dict) -> Report:
        """
        情報を多角的に分析し、レポートの各項目を一つずつ思考しながら埋めていく。
        """
        self.report = Report(
            title=self.region_summary.title or "",
            background="",
            tourist_data_summary="",
            potential_needs="",
            potential_seeds="",
            target_layer="",
        )

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
        report_constraints = (
            "\n【制約条件】\n"
            "- 挨拶や前置きは不要。分析結果のみを出力すること。\n"
            "- 文体は「だ・である」調とすること。\n"
            "- 項目ごとに見出し（###）を立てて記述せよ。"
        )

        self.report.background = self._ask_sequential(
            conversation_history,
            f"以下の情報を元に、このプロジェクトの『調査背景（400字程度）』として記述してください。\n\n情報:\n{project_info}",
            common_constraints=report_constraints,
        )

        self.report.tourist_data_summary = self._ask_sequential(
            conversation_history,
            "既知の課題と現在の問題を踏まえた上で、現在の観光客の行動や傾向を分析してください。",
            common_constraints=report_constraints,
        )

        # --- ステップ2: ターゲット層に関する分析 ---
        future_plan = f"【将来計画】: {current_situation['future_plan']}"
        self.report.target_layer = self._ask_sequential(
            conversation_history,
            "将来計画と各世代の特徴を踏まえて、このプロジェクトの『ターゲット層に関する分析（400字程度）』として記述してください。\n\n"
            f"将来計画:\n{future_plan}\n\n"
            "世代特徴:\n"
            "- 子供世代: 歴史よりも自然に興味を持つ傾向がある。知識が乏しいため、歴史上の人物や歴史上の出来事は知らない可能性がある。\n"
            "- 若年世代: 歴史や文化に対する関心が薄い傾向がある。SNSなどで話題になっているスポットやアミューズメント性の高い体験を求める傾向がある。\n"
            "- 中年世代: 歴史的な町並みや落ち着いた雰囲気を好む傾向があり、一般的レベルの歴史や自然の知識を有している可能性がある。トリビア的な要素を好む傾向がある\n"
            "- 高齢世代: 歴史や文化に対する関心が高い傾向がある。地域の伝統や歴史的な背景を理解し、深く知ることを好む傾向がある。",
            common_constraints=report_constraints,
        )

        # --- ステップ3: 観光客データの要約と潜在ニーズ ---
        self.report.potential_needs = self._ask_sequential(
            conversation_history,
            "現状の問題点とターゲット層からそこから推測される『潜在的なニーズ』を分析してください。",
            common_constraints=report_constraints,
        )

        # --- ステップ4: 潜在シーズとターゲット層 ---
        self.report.potential_seeds = self._ask_sequential(
            conversation_history,
            "地域の将来計画や特徴を活かした音声ガイドのコンテンツ制作に向けて『潜在的なシーズ（可能性の種）』を具体的に特定してください。",
            common_constraints=report_constraints,
        )

        self.report.save_json(self.project.results["analysis"])
        return self.report