from pathlib import Path

from .base_agent import BaseAgent
from ..schema.scene import SceneDesign
from ..schema.character import Character
from ..schema.script import ScriptResponse, Script
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..core.project import Project

class WriterAgent(BaseAgent):
    def create_script(self, project: Project, protagonist: Character, duotagonist: Character, scene_design: SceneDesign, duration, rubi_map) -> Script:
        # パスの解決
        prompt_path = PromptUtils.get_path(project.prompt_dir,  PromptType.CREATE_SCRIPT)

        variables = {
            "title": scene_design.title,
            "location": scene_design.location,
            "scene_summary": scene_design.scene_summary,
            "atmosphere": scene_design.atmosphere,
            "narrative_tone": scene_design.narrative_tone,
            "spatial_direction": scene_design.spatial_direction,
            "protagonist_json": protagonist.model_dump_json(indent=2),
            "duotagonist_json": duotagonist.model_dump_json(indent=2),
            "estimated_duration": duration,
            "rubi_json": rubi_map
        }
        response = self._execute(prompt_path, variables, ScriptResponse)
        
        if response.status == "ready" and response.result:
            script_file = project.script_dir / f"{scene_design.order}_scene.json"
            response.result.save_json(script_file)
            return response.result
        else:
            raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")