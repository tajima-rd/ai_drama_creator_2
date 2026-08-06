# lib/core/pipeline.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Tuple

import geopandas as gpd

from ..agent import (
    AnalysisAgent,
    DesignerAgent,
    ArchitectAgent,
    DirectorAgent,
    WriterAgent,
    DialogueAgent,
)
from ..schema import Character, RegionSummary, Report, Agenda, PlotDesign, SceneDesign
from .project import Project


@dataclass
class Agents:
    """パイプライン全体で使い回すエージェント一式。"""
    analyst: AnalysisAgent
    designer: DesignerAgent
    architect: ArchitectAgent
    director: DirectorAgent
    writer: WriterAgent
    dialogue: DialogueAgent


def build_agents(text_generator, voice_generator, project: Project) -> Agents:
    """各エージェントを初期化して Agents にまとめる。"""
    return Agents(
        analyst=AnalysisAgent(text_generator, project),
        designer=DesignerAgent(text_generator, project),
        architect=ArchitectAgent(text_generator, project),
        director=DirectorAgent(text_generator, project),
        writer=WriterAgent(text_generator, project),
        dialogue=DialogueAgent(voice_generator, project),
    )


class StepTimer:
    def __init__(self):
        self.start_time = datetime.now()
        self.previous_time = self.start_time

    def lap(self) -> datetime:
        current_time = datetime.now()
        elapsed_entire = (current_time - self.start_time).total_seconds()
        elapsed_section = (current_time - self.previous_time).total_seconds()
        print(f"[{current_time.strftime('%H:%M:%S')}] Elapsed（entire）: {elapsed_entire:.2f}秒")
        print(f"[{current_time.strftime('%H:%M:%S')}] Elapsed（section）: {elapsed_section:.2f}秒")
        self.previous_time = current_time
        return current_time


# --- 各ステップ ------------------------------------------------------------

def step_analyze_region(agents: Agents, spot_data: gpd.GeoDataFrame) -> RegionSummary:
    print("--- [01] Analyze the region ---")
    print("Analyzing region data from spot_data")
    return agents.analyst.analyze_region(spot_data)


def step_analyze_issues(agents: Agents, current_situation: Dict[str, str]) -> Report:
    print(f"--- [02] Analyze the current issue: {agents.director.project.project_name} ---")
    return agents.analyst.analyze_current_issues(current_situation)


def step_compose_agenda(agents: Agents, report: Report) -> Agenda:
    print("--- [03] Compose the agenda ---")
    agents.designer.report = report
    return agents.designer.compose_agenda()


def step_define_characters(
    agents: Agents,
    agenda: Agenda,
    character_specs: List[Dict[str, str]],
) -> Tuple[Character, Character]:
    print("--- [04] Define the characters ---")
    agents.architect.agenda = agenda
    agents.director.agenda = agenda

    characters: Dict[str, Character] = {}
    for spec in character_specs:
        role_type = spec["role_type"]
        print(f"-- {role_type} --")
        characters[role_type] = agents.architect.define_characters(
            spec["name"],
            role_type,
            spec["bond"],
            spec["definition"],
        )

    protagonist = characters["protagonist"]
    deuteragonist = characters["deuteragonist"]
    return protagonist, deuteragonist


def step_design_plot(
    agents: Agents,
    protagonist: Character,
    deuteragonist: Character,
    region_summary: RegionSummary,
) -> PlotDesign:
    print("--- [05] Design the story plot ---")
    agents.designer.protagonist = protagonist
    agents.designer.deuteragonist = deuteragonist
    agents.designer.region_summary = region_summary
    return agents.designer.design_plot()


def step_create_scenes(
    agents: Agents,
    spot_data: gpd.GeoDataFrame,
    plot_design: PlotDesign,
    protagonist: Character,
    deuteragonist: Character,
) -> List[SceneDesign]:
    print("--- [06] Define the scene settings ---")
    agents.director.plotDesign = plot_design
    agents.director.protagonist = protagonist
    agents.director.deuteragonist = deuteragonist

    agents.director.setup_scenes(spot_data)
    return agents.director.create_scenes()


def step_write_scenarios(
    agents: Agents,
    spot_data: gpd.GeoDataFrame,
    protagonist: Character,
    deuteragonist: Character,
    scenes: List[SceneDesign],
) -> None:
    print("--- [07] Write the scenario ---")
    agents.writer.protagonist = protagonist
    agents.writer.deuteragonist = deuteragonist
    agents.writer.scenes = scenes
    agents.writer.write_scenarios(spot_data)


def step_write_scripts(agents: Agents) -> None:
    print("--- [08] Write the scripts ---")
    agents.writer.write_scripts()


def step_generate_dialogues(
    agents: Agents,
    protagonist_voice: str = "ja-JP-Chirp3-HD-Puck",
    deuteragonist_voice: str = "ja-JP-Chirp3-HD-Zephyr",
    language: str = "japanese",
) -> None:
    print("--- [09] Generate sound drama ---")

    protagonist = agents.architect.protagonist
    deuteragonist = agents.architect.deuteragonist

    protagonist.profile.voice = protagonist_voice
    deuteragonist.profile.voice = deuteragonist_voice

    agents.dialogue.protagonist = protagonist
    agents.dialogue.deuteragonist = deuteragonist
    agents.dialogue.scripts = agents.writer.scripts
    agents.dialogue.language = language

    agents.dialogue.generate_dialogues()