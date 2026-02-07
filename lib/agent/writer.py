import json
import geopandas as gpd

from pathlib import Path

from .base_agent import BaseAgent
from ..schema.scene import SceneDesign
from ..schema.character import Character
from ..schema.script import ScriptResponse, Script
from ..schema.scenario import ScenarioResponse, Scenario
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..core.project import Project

class WriterAgent(BaseAgent):
    def __init__(
            self, 
            generator, 
            project: Project, 
            protagonist: Character=None, 
            duotagonist: Character=None, 
            scenes: list[SceneDesign]=[],
            scenarios: list[Scenario]=[],
            scripts: list[Script]=None
        ):
        super().__init__(generator)
        self.project = project
        self.protagonist = protagonist
        self.duotagonist = duotagonist
        self.scenes = scenes
        self.scenarios = scenarios
        self.scripts = scripts
        
        self.rubi_map = ""
        if self.project.rubi_map.exists():
            with open(self.project.rubi_map, 'r', encoding='utf-8') as f:
                rubi_data = json.load(f)
                self.rubi_map = json.dumps(rubi_data, ensure_ascii=False, indent=2)
        else:
            self.rubi_map = ""
            print(f"Warning: Rubi map file not found at {self.project.rubi_map}")

    def write_scenarios(self, spot_data: gpd.GeoDataFrame) -> list[Scenario]:
        scenarios = []

        for scene in self.scenes:
            order = scene.order
            scenario_file = self.project.scenario_dir / f"{order}_scenario.json"
            
            spot_row = spot_data[spot_data["order"] == order].iloc[0]
            duration = spot_row["visit_time"]

            if not scenario_file.exists():
                scenario = self._create_scenario(scene, duration)
                scenarios.append(scenario)
            else:
                data = self.load_json(scenario_file)
                scenarios.append(Scenario(**data))
        
        self.scenarios = scenarios
        return scenarios

    def write_scripts(self):
        print("--- [07] 台本執筆 (Scenario to Script) ---")
        scripts = []

        for scenario in self.scenarios:
            order = scenario.scene_id
            script_file = self.project.script_dir / f"{order}_script.json"

            if not script_file.exists():
                print(f"Script {order}: {scenario.scene_title} を台本化中...")
                # 修正：Scenarioオブジェクトを直接渡す
                script = self._create_script(scenario)
                scripts.append(script)
            else:
                print(f"Script {order} はロードします。")
                data = self.load_json(script_file)
                scripts.append(Script(**data))

        self.scripts = scripts
        return self.scripts

    def _create_scenario(self, scene_design: SceneDesign, duration: int) -> Scenario:
        prompt_path = PromptUtils.get_path(self.project.prompt_dir, PromptType.CREATE_SCENARIO)

        variables = {
            "title": scene_design.title,
            "scene_id": scene_design.order,
            "location": scene_design.location,
            "scene_summary": scene_design.scene_summary,
            "estimated_duration": duration,
            "protagonist_json": self.protagonist.model_dump_json(indent=2),
            "duotagonist_json": self.duotagonist.model_dump_json(indent=2),
            "atmosphere": scene_design.atmosphere,
            "narrative_tone": scene_design.narrative_tone,
            "spatial_direction": scene_design.spatial_direction,
            "rubi_json": self.rubi_map
        }
        
        response = self._execute(prompt_path, variables, ScenarioResponse)
        
        if response.status == "ready" and response.result:
            scenario_file = self.project.scenario_dir / f"{scene_design.order}_scenario.json"
            response.result.save_json(scenario_file)
            return response.result
        else:
            raise ValueError(f"シナリオ生成失敗: {response.message}")

    def _create_script(self, scenario: Scenario) -> Script:
        prompt_path = PromptUtils.get_path(self.project.prompt_dir, PromptType.CREATE_SCRIPT)

        # 修正：入力変数を scenario_text 主体に絞り込む
        variables = {
            "title": scenario.scene_title,
            "scenario_text": scenario.scenario_text,
            "character_count": scenario.character_count,
            "protagonist_json": self.protagonist.model_dump_json(indent=2),
            "duotagonist_json": self.duotagonist.model_dump_json(indent=2),
            "rubi_json": self.rubi_map
        }
        
        response = self._execute(prompt_path, variables, ScriptResponse)
        
        if response.status == "ready" and response.result:
            script_file = self.project.script_dir / f"{scenario.scene_id}_script.json"
            response.result.save_json(script_file)
            return response.result
        else:
            raise ValueError(f"台本生成失敗: {response.message}")