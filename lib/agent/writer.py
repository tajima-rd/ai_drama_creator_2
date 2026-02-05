import json
import geopandas as gpd

from pathlib import Path

from .base_agent import BaseAgent
from ..schema.scene import SceneDesign
from ..schema.character import Character
from ..schema.script import ScriptResponse, Script
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..core.project import Project

class WriterAgent(BaseAgent):
    def __init__(
            self, 
            generator, 
            project: Project, 
            protagonist: Character=None, 
            duotagonist: Character=None, 
            scenes: list[SceneDesign]=None,
        ):
        super().__init__(generator)
        self.project = project
        self.protagonist = protagonist
        self.duotagonist = duotagonist
        self.scenes = scenes
        
        self.rubi_map = ""
        if self.project.rubi_map.exists():
            with open(self.project.rubi_map, 'r', encoding='utf-8') as f:
                rubi_data = json.load(f)
                self.rubi_map = json.dumps(rubi_data, ensure_ascii=False, indent=2)
        else:
            self.rubi_map = ""
            print(f"Warning: Rubi map file not found at {self.project.rubi_map}")

    def write_scripts(self, spot_data: gpd.GeoDataFrame):
        print("--- [07] 台本執筆 ---")
        scripts = []

        for scene in self.scenes:
            order = scene.order
            script_file = self.project.script_dir / f"{order}_script.json"

            # GISデータから該当スポットの滞在時間を取得
            spot_row = spot_data[spot_data["order"] == order].iloc[0]
            duration = spot_row["visit_time"]

            if not script_file.exists():
                print(f"Script {order}: {scene.location} を執筆中...")
                
                try:
                    script = self._create_script(
                        scene_design=scene,
                        duration=duration                    )
                    print(f"  -> Script {order} saved.")
                    scripts.append(script)
                except Exception as e:
                    print(f"Error at Script {order}: {e}")
                    continue
            else:
                print(f"Script {order}: {scene.location} は既存ファイルからロードします。")
                data = self.load_json(script_file)
                script = Script(**data)
                scripts.append(script)

        return scripts

    def _create_script(self, scene_design, duration) -> Script:
        # パスの解決
        prompt_path = PromptUtils.get_path(self.project.prompt_dir,  PromptType.CREATE_SCRIPT)

        variables = {
            "title": scene_design.title,
            "location": scene_design.location,
            "scene_summary": scene_design.scene_summary,
            "atmosphere": scene_design.atmosphere,
            "narrative_tone": scene_design.narrative_tone,
            "spatial_direction": scene_design.spatial_direction,
            "protagonist_json": self.protagonist.model_dump_json(indent=2),
            "duotagonist_json": self.duotagonist.model_dump_json(indent=2),
            "estimated_duration": duration,
            "rubi_json": self.rubi_map
        }
        response = self._execute(prompt_path, variables, ScriptResponse)
        
        if response.status == "ready" and response.result:
            script_file = self.project.script_dir / f"{scene_design.order}_script.json"
            response.result.save_json(script_file)
            return response.result
        else:
            raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")