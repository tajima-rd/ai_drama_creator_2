import json
import geopandas as gpd

from pathlib import Path

from .base_agent import BaseAgent
from ..schema.scene import SceneDesign
from ..schema.character import Character
from ..schema.script import ScriptResponse, Script
from ..schema.scenario import ScenarioResponse, Scenario
from ..utils.propmpt_utils import PromptType, PromptLoader
from ..core.project import Project

class WriterAgent(BaseAgent):
    def __init__(
            self, 
            text_generator, 
            project: Project, 
            protagonist: Character=None, 
            deuteragonist: Character=None, 
            scenes: list[SceneDesign]=[],
            scenarios: list[Scenario]=[],
            scripts: list[Script]=[]
        ):
        super().__init__(text_generator)
        self.project = project
        self.protagonist = protagonist
        self.deuteragonist = deuteragonist
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
        scenarios = None

        for scene in self.scenes:
            scene_id = scene.scene_id
            scenario_file = self.project.scenario_dir / f"{scene_id}_scenario.json"
            
            if not scenario_file.exists():
                scenario = self._create_scenario(scene)
                scenarios.append(scenario)
            else:
                data = self.load_json(scenario_file)
                scenarios.append(Scenario(**data))
        
        self.scenarios = scenarios
        return scenarios

    def write_scripts(self):
        scripts = None

        for scenario in self.scenarios:
            scene_id = scenario.scene_id
            script_file = self.project.script_dir / f"{scene_id}_script.json"

            if not script_file.exists():
                print(f"Script {scene_id}: Writing the script for '{scenario.title}' ...")
                # 修正：Scenarioオブジェクトを直接渡す
                script = self._create_script(scenario)
                scripts.append(script)
            else:
                print(f"Script '{scene_id}' has already been created. Loading from file...")
                data = self.load_json(script_file)
                scripts.append(Script(**data))

        self.scripts = scripts
        return self.scripts

    def _create_scenario(self, scene: SceneDesign) -> Scenario:
        prompt_path = PromptLoader.get_path(self.project.prompt_dir, PromptType.CREATE_SCENARIO)

        variables = {
            "title": scene.title,
            "scene_id": scene.scene_id,
            "location": scene.location,
            "scene_summary": scene.scene_summary,
            "estimated_duration": scene.duration,
            "protagonist_json": self.protagonist.model_dump_json(),
            "deuteragonist_json": self.deuteragonist.model_dump_json(),
            "atmosphere": scene.atmosphere,
            "narrative_tone": scene.narrative_tone,
            "spatial_direction": scene.spatial_direction,
            "rubi_json": self.rubi_map
        }
        print(f"Writing scenario for Scene {scene.scene_id}: {scene.title}...")
        response = self._execute(prompt_path, variables, ScenarioResponse)
        
        if response.status == "ready" and response.result:
            scenario_file = self.project.scenario_dir / f"{scene.scene_id}_scenario.json"
            scenario = response.result
            scenario.scene_id = scene.scene_id
            scenario.title = scene.title

            scenario.save_json(scenario_file)
            return scenario
        else:
            raise ValueError(f"Failed to create scenario for Scene {scene.scene_id}: {response.message}")

    def _create_script(self, scenario: Scenario) -> Script:
        prompt_path = PromptLoader.get_path(self.project.prompt_dir, PromptType.CREATE_SCRIPT)

        # 修正：入力変数を scenario_text 主体に絞り込む
        variables = {
            "title": scenario.title,
            "scenario_text": scenario.scenario_text,
            "character_count": scenario.character_count,
            "protagonist_json": self.protagonist.model_dump_json(),
            "deuteragonist_json": self.deuteragonist.model_dump_json(),
            "rubi_json": self.rubi_map
        }
        
        response = self._execute(prompt_path, variables, ScriptResponse)
        
        if response.status == "ready" and response.result:
            script_file = self.project.script_dir / f"{scenario.scene_id}_script.json"
            script = response.result
            script.scene_id = scenario.scene_id
            script.title = scenario.title
            script.character_count = scenario.character_count
            script.save_json(script_file)
            return script
        else:
            raise ValueError(f"Failed to create script for Scene {scenario.scene_id}: {response.message}")