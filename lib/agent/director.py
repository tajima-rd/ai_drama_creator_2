import geopandas as gpd

from pathlib import Path

from lib.schema.agenda import Agenda
from lib.schema.review import ReviewResponse

from .base_agent import BaseAgent
from .analyst import AnalysisAgent
from .architect import ArchitectAgent
from .designer import DesignerAgent
from .writer import WriterAgent

from ..schema.response import SimpleResponse
from ..schema.plot import PlotDesign
from ..schema.character import Character
from ..schema.scene import SceneDesignResponse, SceneDesign

from ..utils.propmpt_utils import PromptType, PromptLoader
from ..core.project import Project


class DirectorAgent(BaseAgent):
    def __init__(
            self, 
            text_generator, 
            project: Project, 
            agenda: Agenda=None, 
            plotDesign: PlotDesign = None, 
            protagonist: Character = None, 
            deuteragonist: Character = None,
            scenes: list[SceneDesign] = None
        ):
        super().__init__(text_generator)
        self.project = project
        self.agenda = agenda
        self.plotDesign = plotDesign
        self.protagonist = protagonist
        self.deuteragonist = deuteragonist
        self.scenes = scenes
    
    def show_review_result(self, review_result):
        print(f"Judgement: {review_result.key}")
        print(f"Comments: {review_result.description}")

        if review_result.key != "合格":
            print(f"Modification Requirement: {review_result.value}")
            return
    
    def review_region_summary(self, analyst: AnalysisAgent) -> str:
        prompt_type = PromptType.REVIEW_REGION_SUMMARY
        prompt_path = PromptLoader.get_path(self.project.prompt_dir, prompt_type)

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
    
    def review_character(self, character: Character, user_definition: str) -> ReviewResponse:
        prompt_type = PromptType.REVIEW_CHARACTER
        prompt_path = PromptLoader.get_path(self.project.prompt_dir, prompt_type)

        variables = {
            "story_concept": self.agenda.concept,
            "user_definition": user_definition,
            "age": character.profile.age,
            "gender": character.profile.gender,
            "bond": character.profile.bond,
            "personality": character.profile.personality,
            "cognitive_bias": character.profile.cognitive_bias,
            "value_system": character.profile.value_system,
            "speaking_style": character.profile.speaking_style,
            "background": character.profile.background,
            "knowledge": character.profile.knowledge,
            "experience": character.profile.experience,
            "action": character.profile.action
        }
        
        response = self._execute(prompt_path, variables, ReviewResponse)
        if response.status == "ready" and response.result:
            review_result = response.result
            return review_result
        else:
            raise ValueError(f"AIからのキャラクターレビューに失敗しました: {response.message}")

    def setup_scenes(self, spot_data: gpd.GeoDataFrame):
        self.scenes = []

        for _, row in spot_data.iterrows():
            scene = SceneDesign(
                scene_id=int(row["order"]),
                title="",
                location=row["name"],
                scene_summary="",
                duration=row["duration"],
                facts=row["explanation"],
                instruction=row["instruction"],
            )
            self.scenes.append(scene)

    def create_scenes(self):
        # スポットごとに処理
        for i, spot in enumerate(self.scenes):
            scene_id = spot.scene_id
            scene_file = self.project.scene_dir / f"{scene_id}_scene.json"

            if not scene_file.exists():
                print(f"Generating Scene {scene_id}: {spot.location}...")
                try:
                    print(f"  -> Creating scene plot...")
                    scene_plot = self._create_scene_plot(spot)
                    self.scenes[i].scene_plot = scene_plot

                    print(f"  -> Creating full scene details...")
                    self.scenes[i] = self._create_scene_setting(spot)

                    print(f"  -> Scene {scene_id} saved.")
                except Exception as e:
                    print(f"Error at Scene {scene_id}: {e}")
                    continue
            else:
                print(f"Scene {scene_id}: {spot.location} has already been created. Loading from file...")
                data = self.load_json(scene_file)
                self.scenes[i] = SceneDesign(**data)

        return self.scenes

    def _create_scene_plot(self, spot) -> str:
        prompt_path = PromptLoader.get_path(self.project.prompt_dir, PromptType.CREATE_SCENE_PLOT)

        variables = {
            "num_scenes": len(self.scenes),
            "scene_number": spot.scene_id,
            "entire_synopsis": self.plotDesign.synopsis,
            "location": spot.location,
            "facts": spot.facts,
            "instruction": spot.instruction,
            "protagonist_json": self.protagonist.model_dump_json(),
            "deuteragonist_json": self.deuteragonist.model_dump_json()
        }

        response = self._execute(prompt_path, variables, SimpleResponse)
        
        if response.status == "ready" and response.result:
            return response.result.value
        else:
            raise ValueError(f"Failed to create scene plot. Response message: {response.message}")

    def _create_scene_setting(self, spot) -> SceneDesign:
        # パスの解決
        prompt_path = PromptLoader.get_path(self.project.prompt_dir,  PromptType.CREATE_SCENE)

        variables = {
            "facts": spot.facts,
            "synopsis": spot.scene_plot,
            "instruction": spot.instruction,
            "emotional_arc": self.plotDesign.emotional_arc,
            "protagonist_json": self.protagonist.model_dump_json(),
            "deuteragonist_json": self.deuteragonist.model_dump_json(),
            "duration": spot.duration
        }

        response = self._execute(prompt_path, variables, SceneDesignResponse)
        
        if response.status == "ready" and response.result:
            this_scene = response.result

            scene_file = self.project.scene_dir / f"{spot.scene_id}_scene.json"
            spot.title = this_scene.title
            spot.scene_summary = this_scene.scene_summary
            spot.atmosphere = this_scene.atmosphere
            spot.narrative_tone = this_scene.narrative_tone
            spot.spatial_direction = this_scene.spatial_direction

            spot.save_json(scene_file)
            return spot
        else:
            raise ValueError(f"Failed to create scene details. Response message: {response.message}")