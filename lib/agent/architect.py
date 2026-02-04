# lib/agent/architect.py
from pathlib import Path

from .base_agent import BaseAgent
from ..schema.agenda import Agenda
from ..schema.character import CharacterResponse, Character
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..core.project import Project

class ArchitectAgent(BaseAgent):
    def create_profile(self, project: Project, agenda: Agenda, data_dict: dict) -> Character:
        # パスの解決
        prompt_path = PromptUtils.get_path(project.prompt_dir, PromptType.CREATE_CHARACTER)

        variables = {
            "agenda": agenda.concept,
            "action": data_dict["action"],
            "role_type": data_dict["role_type"],
            "name": data_dict["name"],
            "voice": data_dict["voice"],
            "bond": data_dict["bond"],
            "gender": data_dict["gender"],
            "personality": data_dict["personality"],
            "age": data_dict["age"],
            "speaking_style": data_dict["speaking_style"],
            "catchphrase": data_dict["catchphrase"],
            "background": data_dict["background"],
            "knowledge": data_dict["knowledge"],
            "experience": data_dict["experience"],
            "extra_settings": data_dict["extra_settings"],
            "relationships": data_dict["relationships"],
        }
        
        response = self._execute(prompt_path, variables, CharacterResponse)
        
        if response.status == "ready" and response.result:
            if data_dict["role_type"] == "protagonist":
                response.result.save_json(project.results["protagonist"])
            elif data_dict["role_type"] == "duotagonist":
                response.result.save_json(project.results["duotagonist"])
            return response.result
        else:
            raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")
