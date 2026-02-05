# lib/agent/analyst.py
import geopandas as gpd

from pathlib import Path

from .base_agent import BaseAgent
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..schema.report import ReportResponse, Report
from ..schema.geography import RegionSummaryResponse, RegionSummary
from ..core.project import Project

class AnalysisAgent(BaseAgent):
    def __init__(self, generator, project: Project):
        super().__init__(generator)
        self.project = project
    
    def analyze_current_issues(self, current_issues:str):
        analysis_path = self.project.results["analysis"]

        if not analysis_path.exists():
            # --- 生成モード ---
            report = self._create_report(current_issues)
            print(f"Analysis result generated and saved to: {analysis_path}")
        else:
            # --- ロードモード ---
            # BaseAgentの静的メソッド（または単なるjson.load）を使って復元
            analysis_data = self.load_json(analysis_path)
            report = Report(**analysis_data)
            print(f"Analysis result loaded from: {analysis_path}")
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
            self.region_summary = self._create_region_summary(spot_list)
            print(f"Region analysis saved to: {analysis_path}")
        else:
            # ロードモード（既にある場合は再利用）
            data = self.load_json(analysis_path)
            # JSONから RegionSummary オブジェクトに復元
            self.region_summary = RegionSummary(**data)
            print(f"Region analysis loaded from: {analysis_path}")
        
        return self.region_summary

    def _create_report(self, current_situation: dict) -> Report:
        # パスの解決
        prompt_path = PromptUtils.get_path(self.project.prompt_dir, PromptType.CREATE_REPORT)

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
        prompt_path = PromptUtils.get_path(self.project.prompt_dir, PromptType.CREATE_REGION_SUMMARY)

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