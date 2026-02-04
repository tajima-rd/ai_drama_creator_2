# lib/agent/analyst.py
from pathlib import Path

from .base_agent import BaseAgent
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..schema.report import ReportResponse, Report
from ..core.project import Project

class AnalysisAgent(BaseAgent):
    def create_report(self, project: Project, regional_info: str) -> Report:
        # パスの解決
        prompt_path = PromptUtils.get_path(project.prompt_dir, PromptType.CREATE_REPORT)

        # 変数の組み立て
        variables = {
            "regional_info": regional_info,
            "project_overview": project.description
        }
    
        # 実行（BaseAgentの_executeを呼び出し）
        response = self._execute(prompt_path, variables, ReportResponse)
        
        if response.status == "ready" and response.result:
            response.result.save_json(project.results["analysis"])
            return response.result
        else:
            # エラーメッセージを「分析レポート」に修正
            raise ValueError(f"AIからの分析レポート生成に失敗しました: {response.message}")