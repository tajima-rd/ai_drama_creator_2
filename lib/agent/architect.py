# lib/agent/architect.py
from .base_agent import BaseAgent
from ..core.project import Project
from ..schema import (
    Agenda,
    Character,
    Profile,
)

class ArchitectAgent(BaseAgent):
    def __init__(self, text_generator, project: Project, agenda: Agenda=None):
        super().__init__(text_generator)
        self.project = project
        self.agenda = agenda
        empty_profile_kwargs = dict(
            name="", bond="", age="", gender="", personality="",
            speaking_style="", background="", knowledge="", experience="",
            cognitive_bias="", value_system="", action="",
        )
        self.protagonist = Character(role_type="protagonist", profile=Profile(**empty_profile_kwargs))
        self.deuteragonist = Character(role_type="deuteragonist", profile=Profile(**empty_profile_kwargs))

    def define_characters(
            self, 
            character_name: str,
            role_type: str,
            bond: str,
            user_definition: str
        ) -> Character:
        char_path = self.project.results[role_type]

        if not char_path.exists():
            # 生成モード
            if role_type == "protagonist":
                self.protagonist.role_type = "protagonist"
                self.protagonist.profile.bond = bond
                self.protagonist.profile.name = character_name
                self._create_profile_sequential(self.protagonist, bond, user_definition)
                return self.protagonist
            elif role_type == "deuteragonist":
                self.deuteragonist.role_type = "deuteragonist"
                self.deuteragonist.profile.bond = bond
                self.deuteragonist.profile.name = character_name
                self._create_profile_sequential(self.deuteragonist, bond, user_definition)
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
        
    def _create_profile_sequential(self, character, bond, user_definition) -> Character:
        context = (
            "あなたは物語キャラクター設計に特化したキャラクターアーキテクトです。\n"
            "生成AIによる自動物語生成のための登場人物を作成します。平易で解りやすい言葉を使用し、"
            "中学生でも理解できるような語彙の範囲で記述してください。\n\n"
            f"【ストーリー概念】\n{self.agenda.concept}\n\n"
            f"【キャラクターの役割】{character.role_type}\n"
            f"【キャラクターの名前】{character.profile.name}\n"
            f"【相方との関係性】{bond}\n"
            f"【キャラクターの基礎設定】\n{user_definition}\n"
        )
        conversation_history = [{"role": "system", "content": context}]

        common_constraints = (
            "\n\n【制約条件】\n"
            "- 挨拶や前置きは不要。本文のみを出力してください。\n"
            "- 与えられた基礎設定を逸脱したり、矛盾した設定を追加しないでください。\n"
            "- 「友達が多い」といった抽象的な表現を避け、具体的なエピソードを想起させる記述をしてください。\n"
            "- 擬音語など、音声合成の障害となる要素は含めないでください。\n"
            "- 具体的な場所については含めないでください。\n"
        )

        character.profile.age = self._ask_sequential(
            conversation_history,
            "このキャラクターの『年齢』を設定してください。不詳でも構いません。",
            "（一言で）", common_constraints, min_length=1,
        )
        character.profile.gender = self._ask_sequential(
            conversation_history,
            "このキャラクターの『性別』を設定してください。不詳や架空の性別でも構いません。",
            "（一言で）", common_constraints, min_length=1,
        )
        character.profile.personality = self._ask_sequential(
            conversation_history,
            "このキャラクターの『性格』を、具体的なエピソードが想起できるように記述してください。",
            "（100字程度）", common_constraints,
        )
        character.profile.background = self._ask_sequential(
            conversation_history,
            "このキャラクターの『経歴』を記述してください。",
            "（150字程度）", common_constraints,
        )
        character.profile.knowledge = self._ask_sequential(
            conversation_history,
            "このキャラクターが持つ『知識』（何を知っていて、何を知らないか）を記述してください。",
            "（100字程度）", common_constraints,
        )
        character.profile.experience = self._ask_sequential(
            conversation_history,
            "このキャラクターの『経験』（誕生から現在までの経験）を記述してください。",
            "（100字程度）", common_constraints,
        )
        character.profile.cognitive_bias = self._ask_sequential(
            conversation_history,
            "このキャラクターが『事実をどう歪めて捉えるか』という認知の歪みのルールを記述してください。"
            "生成AIがこのキャラクターを演じる際の指針となるように、具体的に記述してください。",
            "（150字程度）", common_constraints,
        )
        character.profile.value_system = self._ask_sequential(
            conversation_history,
            "このキャラクターが『何を良しとし、何を嫌うか』という価値観を記述してください。",
            "（100字程度）", common_constraints,
        )
        character.profile.speaking_style = self._ask_sequential(
            conversation_history,
            "このキャラクターの『話し方』の特徴を記述してください。",
            "（100字程度）", common_constraints,
        )
        character.profile.action = self._ask_sequential(
            conversation_history,
            "このキャラクターの『行動様式』（舞台の中での具体的な行動パターン）を記述してください。",
            "（150字程度）", common_constraints,
        )

        if character.role_type == "protagonist":
            character.save_json(self.project.results["protagonist"])
        elif character.role_type == "deuteragonist":
            character.save_json(self.project.results["deuteragonist"])

        return character