import geopandas as gpd

from pathlib import Path
from dotenv import load_dotenv

from lib.core.project import Project
from lib.core.pipeline import (
    build_agents,
    StepTimer,
    step_analyze_region,
    step_analyze_issues,
    step_compose_agenda,
    step_define_characters,
    step_design_plot,
    step_create_scenes,
    step_write_scenarios,
    step_write_scripts,
    step_generate_dialogues,
)
from lib.genai.factory import build_text_generator, build_voice_generator


def init_project() -> Project:
    # 環境設定のロード
    # main.py の場所を起点にして絶対パスを作る
    current_dir = Path(__file__).resolve().parent
    env_path = current_dir / "configure" / "system" / "genai.env"

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"Loaded .env from: {env_path}")
    else:
        print(f"ERROR: .env file NOT FOUND at: {env_path}")

    # プロジェクト設定のロード
    config_path = Path("project/project.json")
    project = Project.load_from_json(config_path)

    print(f"プロジェクト名: {project.project_name}")
    print(f"データ保存先: {project.output_dir}")

    return project


def build_current_situation() -> dict:
    """
    地域の現状分析にあたって前提とする、既知の課題・問題・将来計画。
    プロジェクトごとに変わる想定のため、将来的には project.json 側に
    移すことも検討できるが、いったんはここに定数として置いておく。
    """
    return {
        "known_issues": (
            "多くの観光客が訪れるが、実際には昼食のみが目的化している。"
            "滞在時間は短く、経済効果が限定的であるため、出石そば以外の魅力を"
            "発信することが必要となっている。観光客の年齢層も高い傾向がある。"
        ),
        "problems": (
            "特に、伝統的な町並み、永楽館、福富家住宅、明治館、家老屋敷などの"
            "魅力を十分に活かしきれていないのが課題である。"
        ),
        "future_plan": (
            "少子高齢化社会の現状を考えると、今後は若い世代を中心により広い層に"
            "向けて情報を発信する必要がある。"
        ),
    }


def build_character_specs() -> list[dict]:
    """
    プロタゴニスト・デュオタゴニストの初期設定。
    role_type は必ず "protagonist" と "deuteragonist" を1件ずつ含めること。
    """
    return [
        {
            "role_type": "protagonist",
            "name": "コスモ",
            "bond": "相方の「テスラ」とは、学生時代からの同級生で、いつも間違いを正してもらっている。",
            "definition": (
                "宇宙から飛来した宇宙人。男性。地球に来たばかりなので、地球の知識が"
                "全く無いので、目に映るすべてのものを、全く別のものと認識してしまう。"
                "勝手な想像で的外れなことしか言わず、周りを惑わしたり、劇中では笑いを"
                "誘う役割を持つ。"
            ),
        },
        {
            "role_type": "deuteragonist",
            "name": "テスラ",
            "bond": "相方の「コスモ」とは、学生時代からの同級生で、いつも想像を絶する発言をする「コスモ」に振り回されている。",
            "definition": (
                "宇宙から飛来した宇宙人。女性。地球に来たばかりなので、地球の知識は"
                "全く無い。冷静な常識人。知らないことは手元の端末で即座に調べ、"
                "「コスモ」の暴走を止める役割を持つ。"
            ),
        },
    ]


def main():
    project = init_project()

    text_generator = build_text_generator(project)
    voice_generator = build_voice_generator(project)

    agents = build_agents(text_generator, voice_generator, project)

    spot_data = gpd.read_file(project.gis_data)
    current_situation = build_current_situation()
    character_specs = build_character_specs()

    # --- パイプラインの実行 ---------------------------------------------
    timer = StepTimer()

    region_summary = step_analyze_region(agents, spot_data)
    timer.lap()

    report = step_analyze_issues(agents, current_situation)
    timer.lap()

    agenda = step_compose_agenda(agents, report)
    timer.lap()

    protagonist, deuteragonist = step_define_characters(agents, agenda, character_specs)
    timer.lap()

    plot_design = step_design_plot(agents, protagonist, deuteragonist, region_summary)
    timer.lap()

    scenes = step_create_scenes(agents, spot_data, plot_design, protagonist, deuteragonist)
    timer.lap()

    step_write_scenarios(agents, spot_data, protagonist, deuteragonist, scenes)
    timer.lap()

    step_write_scripts(agents)
    timer.lap()

    # --- 音声生成 -----------------------------------------------------
    # 台本からの実際の音声ファイル生成は処理に時間がかかるため、
    # 既定では実行しない。実行したい場合は、以下のコメントを外すこと。
    # step_generate_dialogues(
    #     agents,
    #     protagonist_voice="ja-JP-Chirp3-HD-Puck",
    #     deuteragonist_voice="ja-JP-Chirp3-HD-Zephyr",
    # )
    # timer.lap()


if __name__ == "__main__":
    main()