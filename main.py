import os
import json
import time
import geopandas as gpd

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum

# core / schema / genai
from lib.core.project import Project
from lib.genai.api_client import GeminiApiClient, ApiKeyManager, LlamaCppApiClient, Qwen3TTSApiClient, GcpTTSApiClient
from lib.genai.generators import QwenSoundGenerator, WriteConfig, GeminiTextGenerator, LlamaCppTextGenerator, GcpSoundGenerator
from lib.schema.character import Character

# agents
from lib.agent.analyst import AnalysisAgent
from lib.agent.designer import DesignerAgent
from lib.agent.architect import ArchitectAgent
from lib.agent.director import DirectorAgent
from lib.agent.writer import WriterAgent
from lib.agent.actor import ActorAgent, DialogueAgent


api_key = ""
config_path = Path("/home/yufujimoto/Git/ai_drama_creator_2/project/project.json") 

def watcher(start_time, previous_time):
    current_time = datetime.now()
    elapsed_ent = current_time - start_time
    elapsed_sec = current_time - previous_time

    print(f"[{current_time.strftime('%H:%M:%S')}] Elapsed（entire）: {elapsed_ent.total_seconds():.2f}秒")
    print(f"[{current_time.strftime('%H:%M:%S')}] Elapsed（section）: {elapsed_sec.total_seconds():.2f}秒")

    return current_time

def init_project():
    # 環境設定のロード
    # 💡 main.py の場所を起点にして絶対パスを作る
    current_dir = Path(__file__).resolve().parent
    env_path = current_dir / "configure" / "system" / "genai.env"

    # 2. ロードを実行し、結果を確認する
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        raw_key = os.getenv("LLAMA_API_KEY")
        print(f"Loaded .env from: {env_path}")
    else:
        print(f"ERROR: .env file NOT FOUND at: {env_path}")
    
    # 読み込み
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"Warning: .env file not found at {env_path}")
    
    # プロジェクト設定のロード
    config_path = Path("project/project.json")
    project = Project.load_from_json(config_path)
    
    print(f"プロジェクト名: {project.project_name}")
    print(f"データ保存先: {project.output_dir}")

    return project

def load_llm_client(project: Project):
    """
    プロジェクト設定に基づいて、適切なLLMクライアントとジェネレーターを初期化する
    """
    # 1. APIキーなどの機密情報は環境変数から取得
    # (LlamaCppなどローカルAPIの場合はダミーでも可)
    gemini_key = os.getenv("GENAI_API_KEY")
    llama_key = os.getenv("LLAMA_API_KEY", "dummy") # デフォルト値を設定可能
    generator = None

    # 3. ジェネレーターの初期化
    write_config = WriteConfig(temperature=0.7) 

    # 2. クライアントの切り替え
    if project.llm_client == "LlamaCpp":
        client = LlamaCppApiClient(
            api_key=llama_key, 
            model_name=project.llm_model, 
            api_url=project.llm_api
        )
        generator = LlamaCppTextGenerator(api_client=client, write_config=write_config)
    elif project.llm_client == "Gemini":
        client = GeminiApiClient(
            api_key=gemini_key, 
            model_name=project.llm_model
        )
        generator = GeminiTextGenerator(api_client=client, write_config=write_config)
    else:
        raise ValueError(f"未対応のLLMクライアントです: {project.llm_client}")
    
    return generator

def load_tts_client(project: Project):
    tts_key = os.getenv("TTS_API_KEY", "dummy") # デフォルト値を設定可能
    generator = None

    # 2. クライアントの切り替え
    if project.tts_client == "Qwen3TTS":
        client = Qwen3TTSApiClient(
            model_name=project.tts_model,
            api_url=project.tts_api,
            api_key=tts_key
        )
        print(f"Initialized Qwen3TTSApiClient with model: {project.tts_model} and API URL: {project.tts_api}")
        generator = QwenSoundGenerator(api_client=client)
    elif project.tts_client == "GCPTTS":
        client = GcpTTSApiClient(
            api_key="dummy",
            model_name=project.tts_model,
            api_config_file=project.secret_dir / "gcp_tts_credentials.json"
        )
        print(f"Initialized GcpTTSApiClient with model: {project.tts_model}")
        generator = GcpSoundGenerator(api_client=client)
    else:
        raise ValueError(f"未対応のTTSクライアントです: {project.tts_client}")
        return None

    return generator

def main():
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] --- 処理を開始します ---")

    # Initialyzing the project
    project = init_project()

    # Initialyzing the generational agent
    text_generator = load_llm_client(project)
    voice_generator = load_tts_client(project)

    # Load agents
    analyst = AnalysisAgent(text_generator, project)
    designer = DesignerAgent(text_generator, project)
    architect = ArchitectAgent(text_generator, project)
    director = DirectorAgent(text_generator, project)
    writer = WriterAgent(text_generator, project)
    actor = ActorAgent(voice_generator, project)
    dialogue = DialogueAgent(voice_generator, project)

    # Show the time for initializing
    previous_time = watcher(start_time, start_time)

    # --- Run Pipeline ---
    # Run the analysis agent
    print(f"--- [01] Analyze the region ---")
    spot_data = gpd.read_file(project.gis_data)

    print("Analyzing region data from:", project.gis_data)
    analyst.analyze_region(spot_data)

    # print("Reviewing the region summary...")
    # director.review_region_summary(analyst)

    # Show the time for analyzing
    previous_time = watcher(start_time, previous_time)

    print(f"--- [02] Analyze the current issue: {project.project_name} ---")
    # Run the analysis agent
    current_situation = {
        "known_issues": "多くの観光客が訪れるが、実際には昼食のみが目的化している。滞在時間は短く、経済効果が限定的であるため、出石そば以外の魅力を発信することが必要となっている。観光客の年齢層も高い傾向がある。",
        "problems":"特に、伝統的な町並み、永楽館、福富家住宅、明治館、家老屋敷などの魅力を十分に活かしきれていないのが課題である。",
        "future_plan":"少子高齢化社会の現状を考えると、今後は若い世代を中心により広い層に向けて情報を発信する必要がある。"
    }
    report = analyst.analyze_current_issues(current_situation)
    
    # Show the time for analyzing
    previous_time = watcher(start_time, previous_time)  # 参考時間：[21:30:11] 経過時間: 3.67秒
    
    print("--- [03] Compose the agenda ---")
    # Run the designer agent
    designer.report = report
    agenda = designer.compose_agenda()

    # Show the time for composing the agenda
    previous_time = watcher(start_time, previous_time)  

    print("--- [04] Setup scene settings ---")
    director.setup_scenes(spot_data)

    print("--- [05] Define the characters---")
    architect.agenda = agenda
    director.agenda = agenda

    print("-- Protagonist --")
    role_type_protagonist = "protagonist"
    character_name = "ほげほげ"
    relation_to_deuteragonist = "相方の「ふがふが」とは、学生時代からの同級生で、いつも間違いを正してもらっている。"
    protagonist_definition = "宇宙から飛来した宇宙人。男性。地球に来たばかりなので、地球の知識が全く無いので、目に映るすべてのものを、全く別のものと認識してしまう。勝手な想像で的外れなことしか言わず、周りを惑わしたり、劇中では笑いを誘う役割を持つ。"
    protagonist = architect.define_characters(
        character_name, 
        role_type_protagonist, 
        relation_to_deuteragonist, 
        protagonist_definition)
    
    print("-- Reviewing the protagonist --")
    try:
        protagonist_review = director.review_character(protagonist, protagonist_definition)
        print("-- Modifying the protagonist based on the review result --")
        architect.modify_character(role_type_protagonist, protagonist_review)
    except ValueError as e:
        print(f"[SKIP] Protagonistのレビュー/修正をスキップしました: {e}")
    
    print("-- deuteragonist --")
    role_type_deuteragonist = "deuteragonist"
    character_name = "ふがふが"
    relation_to_protagonist = "相方の「ほげほげ」とは、学生時代からの同級生で、いつも想像を絶する発言をする「ほげほげ」に振り回されている。"
    deuteragonist_definition = "宇宙から飛来した宇宙人。女性。地球に来たばかりなので、地球の知識は全く無い。冷静な常識人。知らないことは手元の端末で即座に調べ、「ほげほげ」の暴走を止める役割を持つ。"

    deuteragonist = architect.define_characters(
        character_name, 
        role_type_deuteragonist, 
        relation_to_protagonist, 
        deuteragonist_definition)

    print("-- Reviewing the deuteragonist --")
    try:
        deuteragonist_review = director.review_character(deuteragonist, deuteragonist_definition)
        print("-- Modifying the deuteragonist based on the review result --")
        architect.modify_character(role_type_deuteragonist, deuteragonist_review)
    except ValueError as e:
        print(f"[SKIP] Deuteragonistのレビュー/修正をスキップしました: {e}")

    # Show the time for composing the agenda
    previous_time = watcher(start_time, previous_time)  

    print("--- [05] Design the story plot ---")
    # Run the designer agent
    designer.protagonist = protagonist
    designer.deuteragonist = deuteragonist
    designer.region_summary = analyst.region_summary
    plot_design = designer.design_plot()

    # Show the time for designing the plot
    previous_time = watcher(start_time, previous_time)  

    print("--- [06] Define the scene settings ---")
    director.plotDesign = plot_design
    director.protagonist = protagonist
    director.deuteragonist = deuteragonist

    scenes = director.setup_scenes(spot_data)
    scenes = director.create_scenes()

    # 進行状況の表示
    previous_time = watcher(start_time, previous_time)

    print("--- [07] Write the scenario ---")
    writer.protagonist = protagonist
    writer.deuteragonist = deuteragonist
    writer.scenes = scenes

    writer.write_scenarios(spot_data)

    # Show the time for writing the scenario
    previous_time = watcher(start_time, previous_time)

    print("--- [08] Write the scripts ---")
    writer.write_scripts()

    previous_time = watcher(start_time, previous_time)

    # print("--- [09] Generate sound drama ---")
    # protagonist.profile.voice = "ja-JP-Chirp3-HD-Puck"
    # deuteragonist.profile.voice = "ja-JP-Chirp3-HD-Zephyr"

    # dialogue.protagonist = protagonist
    # dialogue.deuteragonist = deuteragonist
    # dialogue.scripts = writer.scripts
    # dialogue.language = "japanese"

    # dialogue.generate_dialogues()

    # watcher(start_time, previous_time)

if __name__ == "__main__":
    main()