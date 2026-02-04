
from pathlib import Path

from .base_agent import BaseAgent
from ..schema.report import Report
from ..schema.agenda import AgendaResponse, Agenda
from ..schema.plot import PlotResponse, PlotDesign
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..core.project import Project

class DesignerAgent(BaseAgent):
    def create_agenda(self, project: Project, report:Report) -> Agenda:
        # パスの解決
        prompt_path = PromptUtils.get_path(project.prompt_dir,  PromptType.CREATE_AGENDA)

        variables = {
            "background": report.background,
            "needs": report.potential_needs,
            "seeds": report.potential_seeds,
            "target": report.target_layer,
        }

        response = self._execute(prompt_path, variables, AgendaResponse)
        
        if response.status == "ready" and response.result:
            response.result.save_json(project.results["agenda"])
            return response.result
        # DesignerAgent.create_agenda の最後
        else:
            raise ValueError(f"AIからの企画構成案の生成に失敗しました: {response.message}")

    # def create_plot(self, project: Project, data_dict: dict) -> PlotDesign:
    #     prompt_path = PromptUtils.get_path(project.prompt_dir,  PromptType.CREATE_PLOT)

    #     variables = {
    #         "planning": data_dict["planning"],
    #         "concept": data_dict["concept"],
    #         "protagonist_json": data_dict["character"]["protagonist"].model_dump_json(indent=2),
    #         "duotagonist_json": data_dict["character"]["duotagonist"].model_dump_json(indent=2),
    #         "spots_info_json": data_dict["spots_info"].model_dump_json(indent=2)
    #     }

    #     response = self._execute(prompt_path, variables, PlotResponse)
        
    #     if response.status == "ready" and response.result:
    #         response.result.save_json(project.results["plot"])
    #         return response.result
    #     else:
    #         raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")
