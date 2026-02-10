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
from lib.genai.api_client import GeminiApiClient, ApiKeyManager, LlamaCppApiClient, Qwen3TTSApiClient
from lib.genai.generators import WriteConfig, GeminiTextGenerator, LlamaCppTextGenerator

from lib.genai.qwen_tts_local import Qwen3TTS, ATTENTION_TYPE

from lib.schema.report import Report
from lib.schema.geography import RegionSummary
from lib.schema.agenda import Agenda
from lib.schema.character import Character, VoiceBase
from lib.schema.plot import PlotDesign
from lib.schema.scene import SceneDesign
from lib.schema.script import Script

# agents
from lib.agent.analyst import AnalysisAgent
from lib.agent.designer import DesignerAgent
from lib.agent.architect import ArchitectAgent
from lib.agent.director import DirectorAgent
from lib.agent.writer import WriterAgent

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

    # 2. クライアントの切り替え
    if project.llm_client == "LlamaCpp":
        client = LlamaCppApiClient(
            api_key=llama_key, 
            model_name=project.llm_model, 
            api_url=project.llm_api
        )
    elif project.llm_client == "Gemini":
        client = GeminiApiClient(
            api_key=gemini_key, 
            model_name=project.llm_model
        )
    else:
        raise ValueError(f"未対応のLLMクライアントです: {project.llm_client}")

    # 3. ジェネレーターの初期化
    write_config = WriteConfig(temperature=0.7) 
    generator = LlamaCppTextGenerator(api_client=client, write_config=write_config)
    
    return generator

def load_tts_client(project: Project):
    """
    プロジェクト設定に基づいて、適切なTTSクライアントを初期化する
    """
    # 1. APIキーなどの機密情報は環境変数から取得
    tts_key = os.getenv("TTS_API_KEY", "dummy") # デフォルト値を設定可能

    # 2. クライアントの切り替え
    if project.tts_client == "Qwen3TTS":
        client = Qwen3TTSApiClient(
            model_name=project.tts_model,
            api_url=project.tts_api,
            api_key=tts_key
        )
    else:
        raise ValueError(f"未対応のTTSクライアントです: {project.tts_client}")

    return client

def generate_sound_drama_locally(project:Project, writer: WriterAgent, protagonist:Character, duotagonist:Character, language: str="japanese"):
    # モデル初期化
    tts_model = Qwen3TTS(
        model_name="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        device="cuda:0",
        attention_type=ATTENTION_TYPE.SDPA
    )

    # 各ファイルを処理
    for script in writer.scripts:
        # 出力ファイル名を決定（例：1_audio.wav）
        base_name = script.scene_id + script.title
        output_file = project.drama_dir / f"{base_name}.wav"

        if not os.path.exists(output_file):
            # スクリプトデータの抽出
            dialogues = []
            speakers = []
            intructs = []
            for dialogue in script.body:
                dialogues.append(dialogue.dialogue)
                intructs.append(dialogue.instruct)

                if dialogue.character == protagonist.profile.name:
                    speakers.append("aiden")
                elif dialogue.character == duotagonist.profile.name:
                    speakers.append("ono_anna")
                else:
                    speakers.append("aiden")
                
                if isinstance(language, str):
                    language_list = [language] * len(script.body)
                else:
                    language_list = language

            # 音声合成
            tts_model.generate(
                file_name=output_file,
                text=dialogues,
                language=language_list,
                speaker=speakers,
                instruct=intructs
            )

            print(f"Sound file generated: {output_file}")
        else:
            print(f"Sound file already exists: {output_file}")

def generate_sound_drama(project:Project, writer: WriterAgent, protagonist:Character, duotagonist:Character, language: str="japanese"):
    # TTSクライアントの初期化（QwenSoundGenerator または Qwen3TTS_RemoteProxy）
    tts_client = load_tts_client(project)

    for script in writer.scripts:
        base_name = str(script.scene_id) + "_" + script.title
        output_file = project.drama_dir / f"{base_name}.wav"

        if not os.path.exists(output_file):
            dialogues = []
            speakers = []
            intructs = []
            
            for dialogue in script.body:
                dialogues.append(dialogue.dialogue)
                intructs.append(dialogue.instruct)

                if dialogue.character == protagonist.profile.name:
                    speakers.append("aiden")
                elif dialogue.character == duotagonist.profile.name:
                    speakers.append("ono_anna")
                else:
                    speakers.append("aiden")
            
            # --- 言語リストの作成は、全てのセリフ（dialogues）を溜めた後に実行 ---
            if isinstance(language, str):
                language_list = [language] * len(dialogues)
            else:
                language_list = language

            # 音声合成（API経由でサーバーへリクエスト）
            tts_client.generate(
                output_path=output_file, # SoundGeneratorの引数名に合わせる場合は output_path
                texts=dialogues,
                languages=language_list,
                speakers=speakers,
                instructs=intructs
            )

            print(f"Sound file generated: {output_file}")
        else:
            print(f"Sound file already exists: {output_file}")

def main():
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] --- 処理を開始します ---")

    # Initialyzing the project
    project = init_project()

    # Initialyzing the generational agent
    text_generator = load_llm_client(project)
    load_tts_client(project)

    # Load agents
    analyst = AnalysisAgent(text_generator, project)
    designer = DesignerAgent(text_generator, project)
    architect = ArchitectAgent(text_generator, project)
    director = DirectorAgent(text_generator, project)
    writer = WriterAgent(text_generator, project)

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
        "problmes":"特に、伝統的な町並み、永楽館、福富家住宅、明治館、家老屋敷などの魅力を十分に活かしきれていないのが課題である。",
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

    print("--- [04] Define the characters---")
    architect.agenda = agenda

    print("-- Protagonist --")
    role_type_protagonist = "protagonist"
    protagonist_setting = {
        "role_type": role_type_protagonist,
        "name": "ほげほげ",
        "action": "勝手な想像で的外れなことしか言わず、周りを惑わしたり、劇中では笑いを誘う役割を持つ",
        "voice": "Aiden",
        "personality": "真面目だけれど、アホで自尊心が高い。好奇心が非常に高い。思い込みが激しい。勝手な想像で的外れなことしか言わない。", 
        "cognitive_bias": "地球上で見かけるあらゆるものを、地球人による宇宙侵略の企てだと勘ぐってしまう。地球のことを全く知らないので、「城跡」を「地球人の宇宙侵略基地」と言ったり、食べ物を食べ物以外のなにかと勘違いする。", 
        "value_system": "とにかく、好奇心旺盛で新しいものや、物珍しいものに夢中になる。偉そうではあるが、比較的簡単に納得する。", 
        "dialogue_example": "われは、宇宙で一番高貴な天才である！！わはははは！", 
        "background": "銀河の彼方から飛来した宇宙人。乗っていた宇宙船が有子山に墜落し、調査のために出石の市街に降りてきた。賢いようには見えない。", 
        "bond": "ふがふが",
        "gender": "男",
        "age": "不明",
        "speaking_style": "常に自信満々で、上から目線で話す。",
        "catchphrase": "「任せておけ！」,「まぁ、実は、その可能性も考えていたが．．．」",
        "knowledge": "地球に関する知識は皆無であるため、宇宙基準の知識で考える。頭は良いが、地球の常識とは異なるため、事実からかけ離れたような推測を行う。",
        "experience": "銀河の彼方の星の貴族の一人息子。子供のころから英才教育を受けてきた。彼のミスで宇宙船が有子山に墜落したが、自分が悪いとは思っていない。市街地には地球の調査のために降りてきた。",
        "extra_settings": "なし",
        "relationships": "「ふがふが」を無自覚に困らせることが多い。"
    }
    protagonist = architect.define_characters(role_type_protagonist, protagonist_setting)

    print("-- Duotagonist --")
    role_type_duotagonist = "duotagonist"
    duotagonist_settings = {
        "role_type": role_type_duotagonist,
        "name": "ふがふが",
        "action": "手持ちの端末で正しい情報を検索し説明し、相方が憶測で喋っている内容を訂正し、正しく伝えるという役割を持つ。",
        "voice": "Ono_Anna",
        "personality": "知的で客観的な常識人。いつも冷静に判断することを心がけており、憶測で行動することを避ける。", 
        "cognitive_bias": "地球のことを全く知らないので、あらゆるものを手元のAI端末で検索あるいは分析し、正しい知識を得る。", 
        "value_system": "保守的で得体の知れないものには近づかない。自分の故郷の星が宇宙で一番だと考えている。", 
        "dialogue_example": "「また勝手なことを言って！」, 「ちょっと、待って！ちゃんと調べるから！」", 
        "background": "銀河の彼方から飛来したもう一人の宇宙人。相方と一緒に出石の市街に降りてきた。あまり、地球に興味は無いが、相方の行動や発言に不安を感じてついてきた。", 
        "bond": "ほげほげ",
        "gender": "女",
        "age": "不明",
        "speaking_style": "やや冷淡で機械的な口調",
        "catchphrase": "「本当にそうかしら？」",
        "knowledge": "地球に関する知識ないが、機械の扱いに長けており、地球の常識についても迅速に調べて整理することができる。",
        "experience": "銀河の彼方の星の一般家庭の長女。非常に優秀であるが、何故かトラブルにまきこまれたり、周囲の人間の世話を焼くことが多い。学生時代は常に最優秀学生をキープしていた。",
        "extra_settings": "なし",
        "relationships": "いつも「ほげほげ」の言動に振り回される。"
    }
    duotagonist = architect.define_characters(role_type_duotagonist, duotagonist_settings)

    # Show the time for composing the agenda
    previous_time = watcher(start_time, previous_time)  

    print("--- [05] Design the story plot ---")
    # Run the designer agent
    designer.protagonist = protagonist
    designer.duotagonist = duotagonist
    designer.region_summary = analyst.region_summary
    plot_design = designer.design_plot()

    # Show the time for designing the plot
    previous_time = watcher(start_time, previous_time)  

    print("--- [06] Define the scene settings ---")
    director.plotDesign = plot_design
    director.protagonist = protagonist
    director.duotagonist = duotagonist

    scenes = director.setup_scenes(spot_data)

    # 進行状況の表示
    previous_time = watcher(start_time, previous_time)

    print("--- [07] Write the scenario ---")
    writer.protagonist = protagonist
    writer.duotagonist = duotagonist
    writer.scenes = scenes

    writer.write_scenarios(spot_data)

    # Show the time for writing the scenario
    previous_time = watcher(start_time, previous_time)

    print("--- [08] Write the scripts ---")
    writer.write_scripts()

    previous_time = watcher(start_time, previous_time)

    print("--- [09] Generate sound drama ---")
    generate_sound_drama(project, writer, protagonist, duotagonist, language="japanese")

    watcher(start_time, previous_time)

if __name__ == "__main__":
    main()