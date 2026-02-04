from pathlib import Path
from .base_agent import BaseAgent
from ..schema.plot import PlotDesign
from ..schema.character import Character
from ..schema.scene import SceneDesignResponse, SceneDesign
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..core.project import Project


class DirectorAgent(BaseAgent):
    def create_scene(
            self, 
            project: Project, 
            plot: PlotDesign, 
            protagonist: Character, 
            duotagonist: Character, 
            dict_data: dict
        ) -> SceneDesign:
        # パスの解決
        prompt_path = PromptUtils.get_path(project.prompt_dir,  PromptType.CREATE_SCENE)

        variables = {
            "order": dict_data["order"],
            "facts": dict_data["facts"],
            "instruction": dict_data["instruction"],
            "synopsis": plot.synopsis,
            "emotional_arc": plot.emotional_arc,
            "protagonist_json": protagonist.model_dump_json(indent=2),
            "duotagonist_json": duotagonist.model_dump_json(indent=2),
        }

        response = self._execute(prompt_path, variables, SceneDesignResponse)
        
        if response.status == "ready" and response.result:
            scene_file = project.scene_dir / f"{dict_data["order"]}_scene.json"
            response.result.save_json(scene_file)
            return response.result
        else:
            raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")