# lib/agent/architect.py
from pathlib import Path

from lib.schema.review import Review

from .base_agent import BaseAgent
from ..schema.agenda import Agenda
from ..schema.character import CharacterResponse, Character, Profile
from ..utils.propmpt_utils import PromptType, PromptLoader
from ..core.project import Project

class ArchitectAgent(BaseAgent):
    def __init__(self, text_generator, project: Project, agenda: Agenda=None):
        super().__init__(text_generator)
        self.project = project
        self.agenda = agenda
        self.protagonist = Character(role_type="protagonist", profile=Profile())
        self.deuteragonist = Character(role_type="deuteragonist", profile=Profile())

    def define_characters(
            self, 
            character_name: str,
            role_type: str,
            bond: str,
            user_definition: str
        ) -> Character:
        # project.results から該当するパスを取得 ("protagonist" または "deuteragonist")
        char_path = self.project.results[role_type]

        if not char_path.exists():
            # 生成モード
            if role_type == "protagonist":
                self.protagonist.role_type = "protagonist"
                self.protagonist.profile.bond = bond
                self.protagonist.profile.name = character_name
                self._create_profile(self.protagonist, bond, user_definition)
                return self.protagonist
            elif role_type == "deuteragonist":
                self.deuteragonist.role_type = "deuteragonist"
                self.deuteragonist.profile.bond = bond
                self.deuteragonist.profile.name = character_name
                self._create_profile(self.deuteragonist, bond, user_definition)
                return self.deuteragonist
            else:
                raise ValueError(f"Invalid role_type: {role_type}. Must be 'protagonist' or 'deuteragonist'.")
        else:
            # ロードモード
            char_data = self.load_json(char_path)
            character = Character(**char_data)

            if role_type == "protagonist": 
                self.protagonist = character
            elif role_type == "deuteragonist": 
                self.deuteragonist = character
            
            print(f"{role_type.capitalize()} loaded from file.")
            return character
        
    def modify_character(self, role_type:str, review:Review):
        if role_type == "protagonist":
            character = self.protagonist
        elif role_type == "deuteragonist":
            character = self.deuteragonist
        else:
            raise ValueError(f"Invalid role_type: {role_type}. Must be 'protagonist' or 'deuteragonist'.")

        if review.Judgement[0] == "合格":
            print(f"{role_type.capitalize()} is approved. No modification needed.")
            return character
        else:
            self._modify_profile(character, review)

    def _create_profile(self, character, bond, user_definition) -> Character:
        # パスの解決
        prompt_path = PromptLoader.get_path(self.project.prompt_dir, PromptType.CREATE_CHARACTER)

        variables = {
            "story_concept": self.agenda.concept,
            "character_name": character.profile.name,
            "character_role": character.role_type,
            "bond_with_another_character": character.profile.bond,
            "user_definition": user_definition
        }
        
        response = self._execute(prompt_path, variables, CharacterResponse)
        
        if response.status == "ready" and response.result:
            genarated_character = response.result
            
            character.profile.age = genarated_character.profile.age
            character.profile.gender = genarated_character.profile.gender
            character.profile.personality = genarated_character.profile.personality
            character.profile.cognitive_bias = genarated_character.profile.cognitive_bias
            character.profile.value_system = genarated_character.profile.value_system
            character.profile.speaking_style = genarated_character.profile.speaking_style
            character.profile.background = genarated_character.profile.background
            character.profile.knowledge = genarated_character.profile.knowledge
            character.profile.experience = genarated_character.profile.experience
            character.profile.action = genarated_character.profile.action

            if character.role_type == "protagonist":
                character.save_json(self.project.results["protagonist"])
            elif character.role_type == "deuteragonist":
                character.save_json(self.project.results["deuteragonist"])
        else:
            raise ValueError(f"AIからのプロフィール生成に失敗しました: {response.message}")

    def _modify_profile(self, character, review: Review) -> Character:
        # パスの解決
        prompt_path = PromptLoader.get_path(self.project.prompt_dir, PromptType.MODIFY_CHARACTER)

        variables = {
            "review_comments": review.comments,
            "review_requirements": review.requirements,
            "story_concept": self.agenda.concept,
            "character_name": character.profile.name,
            "bond": character.profile.bond,
            "age": character.profile.age,
            "gender": character.profile.gender,
            "personality": character.profile.personality,
            "cognitive_bias": character.profile.cognitive_bias,
            "value_system": character.profile.value_system,
            "speaking_style": character.profile.speaking_style,
            "background": character.profile.background,
            "knowledge": character.profile.knowledge,
            "experience": character.profile.experience,
            "action": character.profile.action
        }
        
        response = self._execute(prompt_path, variables, CharacterResponse)
        
        if response.status == "ready" and response.result:
            modified_character = response.result
            
            character.profile.age = modified_character.profile.age
            character.profile.gender = modified_character.profile.gender
            character.profile.personality = modified_character.profile.personality
            character.profile.cognitive_bias = modified_character.profile.cognitive_bias
            character.profile.value_system = modified_character.profile.value_system
            character.profile.speaking_style = modified_character.profile.speaking_style
            character.profile.background = modified_character.profile.background
            character.profile.knowledge = modified_character.profile.knowledge
            character.profile.experience = modified_character.profile.experience
            character.profile.action = modified_character.profile.action

            if character.role_type == "protagonist":
                character.save_json(self.project.results["protagonist"])
            elif character.role_type == "deuteragonist":
                character.save_json(self.project.results["deuteragonist"])
        else:
            raise ValueError(f"AIからのプロフィール修正に失敗しました: {response.message}")
        
        return character