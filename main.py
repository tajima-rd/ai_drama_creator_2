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
from lib.genai.api_client import GeminiApiClient, ApiKeyManager, LlamaCppApiClient
from lib.genai.generators import WriteConfig, GeminiTextGenerator, LlamaCppTextGenerator

from lib.genai.tts import Qwen3TTS, ATTENTION_TYPE

from lib.schema.report import Report
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
    elapsed_sec = previous_time - current_time

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

def load_client(project: Project):
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

def AnalyzeCurrentIssue(analyst:AnalysisAgent, project:Project, current_issues:str):
    analysis_path = project.results["analysis"]

    if not analysis_path.exists():
        # --- 生成モード ---
        report = analyst.create_report(project, current_issues)
        print(f"Analysis result generated and saved to: {analysis_path}")
    else:
        # --- ロードモード ---
        # BaseAgentの静的メソッド（または単なるjson.load）を使って復元
        analysis_data = analyst.load_json(analysis_path)
        report = Report(**analysis_data)
        print(f"Analysis result loaded from: {analysis_path}")
    return report

def ComposeAgenda(designer: DesignerAgent, project: Project, report: Report):
    agenda_path = project.results["agenda"]

    if not agenda_path.exists():
        # --- 生成モード ---
        agenda = designer.create_agenda(project, report)
        print(f"Agenda generated and saved to: {agenda_path}")
    else:
        # --- ロードモード ---
        agenda_data = designer.load_json(agenda_path)
        agenda = Agenda(**agenda_data)
        print(f"Agenda loaded from: {agenda_path}")
        
    return agenda

def DefineCharacters(architect: ArchitectAgent, project: Project, agenda: Agenda, role_type: str, data_dict: dict):
    # project.results から該当するパスを取得 ("protagonist" または "duotagonist")
    char_path = project.results[role_type]

    if not char_path.exists():
        print(f"------ {role_type.capitalize()} の作成 ------")
        # 生成モード
        character = architect.create_profile(project, agenda, data_dict)
        print(f"{role_type.capitalize()} result generated and saved.")
    else:
        # ロードモード
        char_data = architect.load_json(char_path)
        character = Character(**char_data)
        print(f"{role_type.capitalize()} loaded from file.")
    
    return character

def main():
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] --- 処理を開始します ---")

    # Initialyzing the project
    project = init_project()

    # Initialyzing the generational agent
    generator = load_client(project)

    # Load agents
    analyst = AnalysisAgent(generator)
    designer = DesignerAgent(generator)
    architect = ArchitectAgent(generator)
    director = DirectorAgent(generator)
    writer = WriterAgent(generator)

    # Show the time for initializing
    previous_time = watcher(start_time, start_time)

    # --- Run Pipeline ---
    print(f"--- [01] Analyze the current issue: {project.project_name} ---")
    # Run the analysis agent
    current_issues = "出石（いずし）は、出石そばが名物で、辰鼓楼（しんころう）という古い時計台がアイコンとなっている。多くの観光客が訪れるが、実際には昼食のみが目的化している。滞在時間は短く、経済効果が限定的であるため、出石そば以外の魅力を発信することが必要となっている。特に、伝統的な町並み、永楽館、福富家住宅、明治館、家老屋敷などの魅力を十分に活かしきれていないのが課題である。観光客の年齢層も高い傾向がある。少子高齢化社会の現状を考えると、今後はもっと若い世代に訴求力を持ったコンテンツを構築することが必要となる。"
    report = AnalyzeCurrentIssue(analyst, project, current_issues)
    
    # Show the time for analyzing
    previous_time = watcher(start_time, previous_time)  # 参考時間：[21:30:11] 経過時間: 3.67秒
    
    print("--- [02] Compose the agenda ---")
    # Run the designer agent
    agenda = ComposeAgenda(designer, project, report)

    # Show the time for composing the agenda
    previous_time = watcher(start_time, previous_time)  

    # print("--- [03] キャラクター設計 ---")
    # Run the designer agent
    role_type_protagonist = "protagonist"
    protagonist_setting = {
        "role_type": role_type_protagonist,
        "name": "ほげほげ",
        "action": "勝手な想像で的外れなことしか言わず、周りを惑わしたり、劇中では笑いを誘う役割を持つ",
        "voice": "Aiden",
        "personality": "真面目だけれど、アホで自尊心が高い。好奇心が非常に高い。思い込みが激しい。勝手な想像で的外れなことしか言わない。", 
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
    protagonist = DefineCharacters(architect, project, agenda, role_type_protagonist, protagonist_setting)

    # デュオタゴニスト（ふがふが）の設定
    role_type_duotagonist = "duotagonist"
    duotagonist_settings = {
        "role_type": role_type_duotagonist,
        "name": "ふがふが",
        "action": "手持ちの端末で正しい情報を検索し説明し、相方が憶測で喋っている内容を訂正し、正しく伝えるという役割を持つ。",
        "voice": "Ono_Anna",
        "personality": "知的で客観的な常識人。いつも冷静に判断することを心がけており、憶測で行動することを避ける。", 
        "background": "銀河の彼方から飛来したもう一人の宇宙人。相方と一緒に出石の市街に降りてきた。あまり、地球に興味は無いが、相方の行動や発言に不安を感じてついてきた。", 
        "bond": "ほげほげ",
        "gender": "女",
        "age": "不明",
        "speaking_style": "やや冷淡で機械的な口調",
        "catchphrase": "「また勝手なことを言って！」, 「ちょっと、待って！ちゃんと調べるから！」",
        "knowledge": "地球に関する知識ないが、機械の扱いに長けており、地球の常識についても迅速に調べて整理することができる。",
        "experience": "銀河の彼方の星の一般家庭の長女。非常に優秀であるが、何故かトラブルにまきこまれたり、周囲の人間の世話を焼くことが多い。学生時代は常に最優秀学生をキープしていた。",
        "extra_settings": "なし",
        "relationships": "いつも「ほげほげ」の言動に振り回される。"
    }
    duotagonist = DefineCharacters(architect, project, agenda, role_type_duotagonist, duotagonist_settings)

    # Show the time for composing the agenda
    previous_time = watcher(start_time, previous_time)  

    # print("--- [04] プロット作成 ---")
    # spot_data = gpd.read_file(project.gis_data)

    # spots_info = []
    # for _, row in spot_data.iterrows():
    #     spots_info.append({
    #         "order": row["order"],  # 順番
    #         "name": row["name"],  # 名
    #         "explanation": row["explanation"],  # 説明
    #         "scene": row["scene"],  # シーン
    #         "visit_time": row["visit_time"],  # シーン
    #         "geometry": row.geometry.__geo_interface__  # GeoJSON形式の座標
    #     })
    
    # if not os.path.exists(plot_file):
    #     # スポット情報をもとに地域概要文章を生成
    #     area_summary = ""
    #     for spot in spots_info:
    #         area_summary += f"{spot['name']}: {spot['explanation']}\n\n"

    #     # 生成した地域概要をJSON形式に変換
    #     spot_data_dict = {
    #         "agenda_json": agenda_res.agenda.model_dump_json(),
    #         "characters_json": json.loads(char_data),  # 文字列をdictに変換
    #         "spots_info_json": area_summary
    #     }

    #     # プロット作成（地域概要文章を含む）
    #     plot_res = designer.create_plot(
    #         project,
    #         spot_data_dict
    #     )

    #     if plot_res.status == "error":
    #         print(f"Error at create an angeda.: {plot_res.message}")
    #         return
        
    #     # 結果を保存
    #     save_json(plot_res.model_dump(), project.output_dir, plot_file)
    #     print("Plot saved to file.")
    # else:
    #     # ロードモード
    #     plot_data = load_json(project.output_dir, plot_file)
    #     plot_res = PlotResponse(**plot_data)  # または AnalysisReport に合わせる
    #     print("Plot loaded from file.") 

    # print("--- [05] シーン設計 ---")
    # if os.path.exists(project.scene_dir):
    #     # スポット情報をもとに地域概要文章を生成
    #     scene_summary = ""
    #     for spot in spots_info:
    #         order = spot["order"]
    #         visit_time = spot["visit_time"]
    #         scene_summary = f"{spot['scene']}"

    #         scene_file = project.scene_dir / f"{order}_scene.json"
            
    #         if not os.path.exists(scene_file):
    #             spot_data_dict = {
    #                 "plot_json": plot_res.model_dump_json(),
    #                 "characters_json": json.loads(char_data),  # 文字列をdictに変換
    #                 "scene_summary": f"{spot['name']}: {scene_summary}",
    #                 "visit_time": visit_time
    #             }

    #             # プロット作成（地域概要文章を含む）
    #             scene_res = director.create_scene(
    #                 project,
    #                 spot_data_dict
    #             )

    #             if scene_res.status == "error":
    #                 print(f"Error at create an scene {order}.: {scene_res.message}")
    #                 return
                
    #             # 結果を保存
    #             save_json(scene_res.model_dump(), project.scene_dir, scene_file)
    #             print(f"Scene {order} saved to file.")

    # current_time = datetime.now()
    # elapsed = current_time - start_time
    # print(f"[{current_time.strftime('%H:%M:%S')}] 経過時間: {elapsed.total_seconds():.2f}秒")

    # print("--- [06] 台本執筆 ---")
    # if os.path.exists(project.script_dir):
    #     # スポット情報をもとに地域概要文章を生成
    #     scene_summary = ""
    #     for spot in spots_info:
    #         order = spot["order"]
    #         visit_time = spot["visit_time"]
    #         spot_summary = f"{spot['name']}: {spot['explanation']}"

    #         script_file = project.script_dir / f"{order}_script.json"

    #         scene_file = project.scene_dir / f"{order}_scene.json"
    #         scene_data = load_json(project.scene_dir, scene_file)
    #         scene_res = SceneResponse(**scene_data)
            
    #         if not os.path.exists(script_file):
    #             scene_data_dict = {
    #                 "scene_json": scene_res.model_dump_json(),
    #                 "spot_data": spot_summary,
    #                 "characters_json": json.loads(char_data),
    #                 "rubi_map": f"{spot['name']}: {scene_summary}"
    #             }

    #             # プロット作成（地域概要文章を含む）
    #             script_res = writer.create_script(
    #                 project,
    #                 scene_data_dict
    #             )

    #             if script_res.status == "error":
    #                 print(f"Error at create an script {order}.: {script_res.message}")
    #                 return
                
    #             # 結果を保存
    #             save_json(script_res.model_dump(), project.script_dir, script_file)
    #             print(f"Script {order} saved to file.")
                
    #         else:
    #             script_data = load_json(project.script_dir, script_file)

    # current_time = datetime.now()
    # elapsed = current_time - start_time
    # print(f"[{current_time.strftime('%H:%M:%S')}] 経過時間: {elapsed.total_seconds():.2f}秒")

    # print("--- [07] 音声生成 ---")
    # # スクリプトファイルをファイル名順でソート
    # script_files = sorted(project.script_dir.glob("*.json"), key=lambda p: int(p.stem.split("_")[0]))

    # # モデル初期化
    # tts_model = Qwen3TTS(
    #     model_name="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    #     device="cuda:0",
    #     attention_type=ATTENTION_TYPE.SDPA
    # )

    # # 各ファイルを処理
    # for script_file in script_files:
    #     with open(script_file, "r", encoding="utf-8") as f:
    #         data = json.load(f)

    #     # 出力ファイル名を決定（例：1_audio.wav）
    #     base_name = script_file.stem.split("_")[0]
    #     output_file = project.drama_dir / f"{base_name}_audio.wav"

    #     if not os.path.exists(output_file):
    #         # スクリプトデータの抽出
    #         script_body = data["script_report"]["script_body"]
    #         texts = [item["dialogue"] for item in script_body]
    #         languages = ["japanese"] * len(texts)

    #         speakers = []
    #         for item in script_body:
    #             character = item["speaker"] 
    #             if character == pro_data_dict["name"]:
    #                 speakers.append(pro_data_dict["voice"])
    #             elif character == duo_data_dict["name"]:
    #                 speakers.append(duo_data_dict["voice"])
    #             else:
    #                 speakers.append("Dylan")

    #         # 音声合成
    #         tts_model.generate(
    #             file_name=output_file,
    #             text=texts,
    #             language=languages,
    #             speaker=speakers
    #         )

    #         print(f"音声ファイルを保存しました: {output_file}")
    #     else:
    #         print(f"音声ファイルは既に存在します: {output_file}")
    
    # current_time = datetime.now()
    # elapsed = current_time - start_time
    # print(f"[{current_time.strftime('%H:%M:%S')}] 経過時間: {elapsed.total_seconds():.2f}秒")

if __name__ == "__main__":
    main()