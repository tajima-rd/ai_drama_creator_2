import geopandas as gpd

from pathlib import Path

from .base_agent import BaseAgent
from .analyst import AnalysisAgent
from .architect import ArchitectAgent
from .designer import DesignerAgent
from .writer import WriterAgent

from ..schema.response import SimpleResponse
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
    
    def show_review_result(self, review_result):
        print(f"Judgement: {review_result.key}")
        print(f"Comments: {review_result.description}")

        if review_result.key != "合格":
            print(f"Modification Requirement: {review_result.value}")
            return
    
    def review_region_summary(self, analyst: AnalysisAgent) -> str:
        prompt_type = PromptType.REVIEW_REGION_SUMMARY
        prompt_path = PromptUtils.get_path(self.project.prompt_dir, prompt_type)

        variables = {
            "title": analyst.region_summary.title,
            "summary": analyst.region_summary.summary,
            "features": analyst.region_summary.features
        }

        response = self._execute(prompt_path, variables, SimpleResponse)
        if response.status == "ready" and response.result:
            self.show_review_result(response.result)
            return response.result
        else:
            raise ValueError(f"AIからの地域概要レビューに失敗しました: {response.message}") 
        

    def setup_scenes(self, spot_data: gpd.GeoDataFrame):
        # 完了したシーンを格納するリスト（後続で使う場合）
        scenes = []

        # スポットごとに処理
        for _, row in spot_data.iterrows():
            scene_id = row["order"]
            scene_file = self.project.scene_dir / f"{scene_id}_scene.json"

            if not scene_file.exists():
                print(f"Generating Scene {scene_id}: {row['name']}...")
                
                # DirectorAgent.create_scene が期待する dict_data の構築
                dict_data = {
                    "scene_id": scene_id,
                    "facts": f"name: {row['name']}\nexplanation: {row['explanation']}",
                    "instruction": f"scene: {row['scene']}\nstay_time: {row['visit_time']}"
                }

                try:
                    scene_design = self._create_scene(dict_data)
                    print(f"  -> Scene {scene_id} saved.")
                    scenes.append(scene_design)
                except Exception as e:
                    print(f"Error at Scene {scene_id}: {e}")
                    # 1つのシーンで失敗しても続行するか、停止するかは要件次第
                    continue
            else:
                # ロードモード
                print(f"Scene {scene_id}: {row['name']} は既存ファイルからロードします。")
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
            "scene_id": dict_data["scene_id"],
            "facts": dict_data["facts"],
            "instruction": dict_data["instruction"],
            "synopsis": self.plotDesign.synopsis,
            "emotional_arc": self.plotDesign.emotional_arc,
            "protagonist_json": self.protagonist.model_dump_json(indent=2),
            "duotagonist_json": self.duotagonist.model_dump_json(indent=2),
        }

        response = self._execute(prompt_path, variables, SceneDesignResponse)
        
        if response.status == "ready" and response.result:
            scene_file = self.project.scene_dir / f"{dict_data["scene_id"]}_scene.json"
            response.result.save_json(scene_file)
            return response.result
        else:
            raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")