import geopandas as gpd

from .base_agent import BaseAgent
from ..core.project import Project
from ..schema import (
    Agenda,
    PlotDesign,
    Character,
    SceneDesign
)

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
                # scene.py 側で必須化したフィールド。この時点ではまだAIの
                # 応答を受け取っていないため、空文字を明示的に渡しておき、
                # _create_scene_setting() の応答を受けて後から上書きされる。
                atmosphere="",
                narrative_tone="",
                spatial_direction="",
            )
            self.scenes.append(scene)

        return self.scenes

    def create_scenes(self):
        # スポットごとに処理
        for i, spot in enumerate(self.scenes):
            scene_id = spot.scene_id
            scene_file = self.project.scene_dir / f"{scene_id}_scene.json"

            if not scene_file.exists():
                print(f"Generating Scene {scene_id}: {spot.location}...")
                try:
                    print(f"  -> Creating scene plot...")
                    scene_plot = self._create_scene_plot_sequential(spot)
                    self.scenes[i].scene_plot = scene_plot

                    print(f"  -> Creating full scene details...")
                    self.scenes[i] = self._create_scene_setting_sequential(spot)

                    print(f"  -> Scene {scene_id} saved.")
                except Exception as e:
                    print(f"Error at Scene {scene_id}: {e}")
                    continue
            else:
                print(f"Scene {scene_id}: {spot.location} has already been created. Loading from file...")
                data = self.load_json(scene_file)
                self.scenes[i] = SceneDesign(**data)

        return self.scenes

    def _create_scene_plot_sequential(self, spot) -> str:
        """
        create_scene_plot.txt（JSON一括生成）の代わりに、対話形式で
        このシーンに該当する部分あらすじ（scene_plot）を生成する。
        """
        protagonist_name = self.protagonist.profile.name
        deuteragonist_name = self.deuteragonist.profile.name

        context = (
            "あなたはストーリー構成と観光体験設計に精通したストーリーデザイナーです。\n"
            "以下の情報のみを根拠として、物語全体のあらすじのうち、このシーンに該当する"
            "部分あらすじだけを作成します。\n\n"
            f"【物語全体のあらすじ】\n{self.plotDesign.synopsis}\n\n"
            f"【このシーンの番号】{spot.scene_id} / 全{len(self.scenes)}シーン中\n"
            f"【舞台となるスポット】{spot.location}\n"
            f"【スポット情報（このシーンの事実の唯一の根拠）】\n{spot.facts}\n\n"
            f"【シーン指示】\n{spot.instruction}\n\n"
            f"【登場人物1：{protagonist_name}】\n{self._describe_character(self.protagonist)}\n\n"
            f"【登場人物2：{deuteragonist_name}】\n{self._describe_character(self.deuteragonist)}\n\n"
        )
        conversation_history = [{"role": "system", "content": context}]

        common_constraints = (
            "\n\n【制約条件】\n"
            "- 挨拶や前置きは不要。本文のみを出力してください。\n"
            f"- 登場人物は必ず実名（{protagonist_name} / {deuteragonist_name}）で呼んでください。\n"
            f"- 舞台は『{spot.location}』のみです。他の場所や建物の名称を登場させないで"
            "ください。\n"
            "- 事実に基づくことを原則とし、上記のスポット情報に書かれていない年号・時代区分・"
            "国名・人物・出来事を創作しないでください。\n"
            "- 物語全体のあらすじと矛盾してはいけません。今回のシーン番号以外のシーンの内容を"
            "書いてはいけません。\n"
        )

        return self._ask_sequential(
            conversation_history,
            f"以下は、このシーンの舞台『{spot.location}』に関するスポット情報です。この内容を"
            f"根拠として、物語全体のあらすじのうち、このシーン（{spot.scene_id}番目）に該当"
            f"する部分だけの『部分あらすじ』を作成してください。\n\n"
            f"--- スポット情報 ---\n{spot.facts}\n--- ここまで ---\n\n",
            common_constraints=common_constraints,
        )

    def _create_scene_setting_sequential(self, spot) -> SceneDesign:
        """
        create_scene.txt（JSON一括生成）の代わりに、SceneDesignの
        title/scene_summary/atmosphere/narrative_tone/spatial_direction
        を1問1答形式で順番に生成する。

        設計方針（個別のエラー事例に対する場当たり的なパッチを避けるため、
        明文化しておく）：
        - 「事実に基づくこと」「実名を使うこと」「この場所以外を登場させ
          ないこと」は、特定の質問（例：scene_summaryだけ）に個別に
          埋め込むのではなく、全ての質問に共通する制約（common_constraints）
          として一律に課す。個別対応は質問ごとに矛盾したルールを生み、
          汎用性を欠く。
        - 前段の回答の形式（番号付きリストの有無など）に依存する参照
          （「直前の(1)〜(4)を踏まえて」等）は行わない。モデルの出力形式は
          安定しないため、そのような参照は容易に壊れる。
        - 独自ロジックによる「原文一致検証」のような、内容を機械的に
          断定する仕組みは設けない。facts の内容は多様であり、汎用的な
          正誤判定は困難で、かえって誤った足切りをしかねない。
        """
        duration_seconds = spot.duration or 0
        duration_minutes = max(1, round(duration_seconds / 60))
        MAX_SUMMARY_LENGTH = 1500
        target_summary_length = min(duration_minutes * 350, MAX_SUMMARY_LENGTH)

        protagonist_name = self.protagonist.profile.name
        deuteragonist_name = self.deuteragonist.profile.name

        context = (
            "あなたは、没入型観光音声ドラマのシーン設計専門ディレクターです。\n"
            "以下の情報のみを根拠として、このシーンの詳細な設計を行います。\n\n"
            f"【舞台となるスポット】{spot.location}\n"
            f"【スポット情報（このシーンの事実の唯一の根拠）】\n{spot.facts}\n\n"
            f"【シーン指示】\n{spot.instruction}\n\n"
            f"【このシーンのあらすじ（部分プロット）】\n{spot.scene_plot}\n\n"
            f"【登場人物1：{protagonist_name}】\n{self._describe_character(self.protagonist)}\n\n"
            f"【登場人物2：{deuteragonist_name}】\n{self._describe_character(self.deuteragonist)}\n\n"
            f"【想定滞在時間】{duration_minutes}分間\n"
        )
        conversation_history = [{"role": "system", "content": context}]

        # 以下の制約は、特定の質問に個別対応するのではなく、
        # この後の全ての質問（scene_summary/atmosphere/narrative_tone/
        # spatial_direction/title）に一律で付与する。
        common_constraints = (
            "\n\n【制約条件】\n"
            "- 挨拶や前置きは不要。本文のみを出力してください。\n"
            "- 文章は「である調」で書いてください。\n"
            f"- 登場人物は必ず実名（{protagonist_name} / {deuteragonist_name}）で"
            "呼んでください。「論理的な人物」のような抽象的な呼び方はしないでください。\n"
            f"- 舞台は『{spot.location}』のみです。他の場所や建物の名称を登場させないで"
            "ください。\n"
            "- 事実に基づくことを原則とし、上記のスポット情報に書かれていない年号・"
            "時代区分・国名・人物・出来事を創作しないでください。スポット情報に無い"
            "ことは、無理に具体的にせず、雰囲気や情緒の描写で補ってください。\n"
        )

        spot.scene_summary = self._ask_sequential(
            conversation_history,
            f"以下は、このシーンの舞台『{spot.location}』に関するスポット情報（史実・具体情報）"
            f"です。この内容を根拠として、このシーンの『概要』を作成してください。\n\n"
            f"--- スポット情報 ---\n{spot.facts}\n--- ここまで ---\n\n"
            f"上記のスポット情報に書かれている具体的な内容（年号・人物名・経緯など）を、"
            f"本文の中で実際に触れてください。二人の登場人物が会話する場面として書いてください。",
            f"（{target_summary_length}文字程度）",
            common_constraints,
        )
        spot.atmosphere = self._ask_sequential(
            conversation_history,
            "このシーンの『現場の雰囲気・空気感』を記述してください。",
            "（100字程度）",
            common_constraints,
        )
        spot.narrative_tone = self._ask_sequential(
            conversation_history,
            "このシーンにおける『登場人物たちの声のトーン』を記述してください。",
            "（100字程度）",
            common_constraints,
        )
        spot.spatial_direction = self._ask_sequential(
            conversation_history,
            "このシーンの『空間演出上の留意点』（歩く速度や視線の誘導など）を記述してください。",
            "（100字程度）",
            common_constraints,
        )
        spot.title = self._ask_title(
            conversation_history,
            "ここまでの内容に合致する、このシーンの『仮タイトル』を1つだけ提案してください。",
            common_constraints,
        )

        scene_file = self.project.scene_dir / f"{spot.scene_id}_scene.json"
        spot.save_json(scene_file)
        return spot