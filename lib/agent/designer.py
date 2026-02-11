
from pathlib import Path

from .base_agent import BaseAgent
from ..schema.report import Report
from ..schema.agenda import AgendaResponse, Agenda
from ..schema.character import Character
from ..schema.plot import PlotResponse, PlotDesign
from ..schema.geography import RegionSummary
from ..utils.propmpt_utils import PromptType, PromptLoader
from ..core.project import Project

class DesignerAgent(BaseAgent):
    def __init__(
            self, 
            generator, 
            project: Project, 
            agenda: Agenda=None, 
            report:Report=None, 
            protagonist: Character = None, 
            duotagonist: Character = None, 
            region_summary: RegionSummary = None
        ):
        
        super().__init__(generator)
        self.project = project
        self.report = report
        self.agenda = agenda
        self.protagonist = protagonist
        self.duotagonist = duotagonist
        self.region_summary = region_summary
    
    def compose_agenda(self):
        agenda_path = self.project.results["agenda"]

        if not agenda_path.exists():
            # --- 生成モード ---
            self.agenda = self._create_agenda()
            print(f"Agenda generated and saved to: {agenda_path}")
        else:
            # --- ロードモード ---
            agenda_data = self.load_json(agenda_path)
            self.agenda = Agenda(**agenda_data)
            print(f"Agenda loaded from: {agenda_path}")
            
        return self.agenda

    def design_plot(self):
        plot_path = self.project.results["plot"]

        if not plot_path.exists():
            plot_design = self._create_plot()
            print(f"Plot generated and saved to: {plot_path}")
        else:
            # ロードモード
            plot_data = self.load_json(plot_path)
            # PlotResponse(封筒)の中身を想定して PlotDesign にパース
            plot_design = PlotDesign(**plot_data)
            print(f"Plot loaded from: {plot_path}")

        return plot_design

    def _create_agenda(self) -> Agenda:
        # パスの解決
        prompt_path = PromptLoader.get_path(self.project.prompt_dir,  PromptType.CREATE_AGENDA)

        variables = {
            "background": self.report.background,
            "needs": self.report.potential_needs,
            "seeds": self.report.potential_seeds,
            "target": self.report.target_layer,
        }

        response = self._execute(prompt_path, variables, AgendaResponse)
        
        if response.status == "ready" and response.result:
            response.result.save_json(self.project.results["agenda"])
            return response.result
        # DesignerAgent.create_agenda の最後
        else:
            raise ValueError(f"AIからの企画構成案の生成に失敗しました: {response.message}")

    def _create_plot(self) -> PlotDesign:
        prompt_path = PromptLoader.get_path(self.project.prompt_dir,  PromptType.CREATE_PLOT)

        variables = {
            "planning": self.agenda.planning,
            "concept": self.agenda.concept,
            "protagonist_json": self.protagonist.model_dump_json(indent=2),
            "duotagonist_json": self.duotagonist.model_dump_json(indent=2),
            "region_summary": self.region_summary.summary,
            "region_feature": self.region_summary.features
        }

        response = self._execute(prompt_path, variables, PlotResponse)
        
        if response.status == "ready" and response.result:
            response.result.save_json(self.project.results["plot"])
            return response.result
        else:
            raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")
