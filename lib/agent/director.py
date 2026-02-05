import geopandas as gpd

from pathlib import Path
from .base_agent import BaseAgent
from ..schema.plot import PlotDesign
from ..schema.character import Character
from ..schema.scene import SceneDesignResponse, SceneDesign
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..core.project import Project


class DirectorAgent(BaseAgent):
    def __init__(
            self, 
            generator, 
            project: Project, 
            plotDesign: PlotDesign = None, 
            protagonist: Character = None, 
            duotagonist: Character = None
        ):
        super().__init__(generator)
        self.project = project
        self.plotDesign = plotDesign
        self.protagonist = protagonist
        self.duotagonist = duotagonist
    
    def setup_scenes(self, spot_data: gpd.GeoDataFrame):
        # 完了したシーンを格納するリスト（後続で使う場合）
        scenes = []

        # スポットごとに処理
        for _, row in spot_data.iterrows():
            order = row["order"]
            scene_file = self.project.scene_dir / f"{order}_scene.json"

            if not scene_file.exists():
                print(f"Generating Scene {order}: {row['name']}...")
                
                # DirectorAgent.create_scene が期待する dict_data の構築
                dict_data = {
                    "order": order,
                    "facts": f"name: {row['name']}\nexplanation: {row['explanation']}",
                    "instruction": f"scene: {row['scene']}\nstay_time: {row['visit_time']}"
                }

                try:
                    scene_design = self._create_scene(dict_data)
                    print(f"  -> Scene {order} saved.")
                    scenes.append(scene_design)
                except Exception as e:
                    print(f"Error at Scene {order}: {e}")
                    # 1つのシーンで失敗しても続行するか、停止するかは要件次第
                    continue
            else:
                # ロードモード
                print(f"Scene {order}: {row['name']} は既存ファイルからロードします。")
                data = self.load_json(scene_file)
                scene_design = SceneDesign(**data)
                scenes.append(scene_design)

        return scenes

    def _create_scene(
            self, 
            dict_data: dict
        ) -> SceneDesign:
        # パスの解決
        prompt_path = PromptUtils.get_path(self.project.prompt_dir,  PromptType.CREATE_SCENE)

        variables = {
            "order": dict_data["order"],
            "facts": dict_data["facts"],
            "instruction": dict_data["instruction"],
            "synopsis": self.plotDesign.synopsis,
            "emotional_arc": self.plotDesign.emotional_arc,
            "protagonist_json": self.protagonist.model_dump_json(indent=2),
            "duotagonist_json": self.duotagonist.model_dump_json(indent=2),
        }

        response = self._execute(prompt_path, variables, SceneDesignResponse)
        
        if response.status == "ready" and response.result:
            scene_file = self.project.scene_dir / f"{dict_data["order"]}_scene.json"
            response.result.save_json(scene_file)
            return response.result
        else:
            raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")