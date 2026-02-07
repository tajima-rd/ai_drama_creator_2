# lib/agent/architect.py
from pathlib import Path

from .base_agent import BaseAgent
from ..schema.agenda import Agenda
from ..schema.character import CharacterResponse, Character
from ..utils.propmpt_utils import PromptType, PromptUtils
from ..core.project import Project

class ArchitectAgent(BaseAgent):
    def __init__(self, generator, project: Project, agenda: Agenda=None):
        super().__init__(generator)
        self.project = project
        self.agenda = agenda

    def define_characters(self, role_type: str, data_dict: dict):
        # project.results から該当するパスを取得 ("protagonist" または "duotagonist")
        char_path = self.project.results[role_type]

        if not char_path.exists():
            # 生成モード
            character = self._create_profile(data_dict)
            print(f"{role_type.capitalize()} result generated and saved.")
        else:
            # ロードモード
            char_data = self.load_json(char_path)
            character = Character(**char_data)
            print(f"{role_type.capitalize()} loaded from file.")
        
        return character
    
    def _create_profile(self, data_dict: dict) -> Character:
        # パスの解決
        prompt_path = PromptUtils.get_path(self.project.prompt_dir, PromptType.CREATE_CHARACTER)

        variables = {
            "agenda": self.agenda.concept,
            "action": data_dict["action"],
            "role_type": data_dict["role_type"],
            "name": data_dict["name"],
            "voice": data_dict["voice"],
            "bond": data_dict["bond"],
            "gender": data_dict["gender"],
            "personality": data_dict["personality"],
            "cognitive_bias": data_dict["cognitive_bias"],
            "value_system": data_dict["value_system"],
            "dialogue_example": data_dict["dialogue_example"],
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
                response.result.save_json(self.project.results["protagonist"])
            elif data_dict["role_type"] == "duotagonist":
                response.result.save_json(self.project.results["duotagonist"])
            return response.result
        else:
            raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")
