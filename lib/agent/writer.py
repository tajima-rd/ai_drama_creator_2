import json
import re
import geopandas as gpd

from .base_agent import BaseAgent
from ..core.project import Project
from ..schema import (
    SceneDesign,
    Character,
    Script,
    Dialogue,
    Scenario
)

class WriterAgent(BaseAgent):
    def __init__(
            self, 
            text_generator, 
            project: Project, 
            protagonist: Character=None, 
            deuteragonist: Character=None, 
            scenes: list[SceneDesign]=None,
            scenarios: list[Scenario]=None,
            scripts: list[Script]=None
        ):
        super().__init__(text_generator)
        self.project = project
        self.protagonist = protagonist
        self.deuteragonist = deuteragonist
        # 可変オブジェクト（list）をデフォルト引数にすると、全インスタンスで
        # 同じリストが共有されてしまう（Pythonの既知の落とし穴）ため、
        # デフォルトは None にし、ここで個別に空リストを生成する。
        self.scenes = scenes if scenes is not None else []
        self.scenarios = scenarios if scenarios is not None else []
        self.scripts = scripts if scripts is not None else []
        
        self.rubi_map = ""
        if self.project.rubi_map.exists():
            with open(self.project.rubi_map, 'r', encoding='utf-8') as f:
                rubi_data = json.load(f)
                self.rubi_map = json.dumps(rubi_data, ensure_ascii=False, indent=2)
        else:
            self.rubi_map = ""
            print(f"Warning: Rubi map file not found at {self.project.rubi_map}")

    def write_scenarios(self, spot_data: gpd.GeoDataFrame) -> list[Scenario]:
        scenarios = []

        for scene in self.scenes:
            scene_id = scene.scene_id
            scenario_file = self.project.scenario_dir / f"{scene_id}_scenario.json"

            if not scenario_file.exists():
                try:
                    scenario = self._create_scenario_sequential(scene)
                    scenarios.append(scenario)
                except Exception as e:
                    print(f"Error at Scenario for Scene {scene_id}: {e}")
                    continue
            else:
                data = self.load_json(scenario_file)
                scenarios.append(Scenario(**data))

        self.scenarios = scenarios
        return scenarios

    def write_scripts(self):
        scripts = []
        scene_by_id = {scene.scene_id: scene for scene in (self.scenes or [])}

        for scenario in self.scenarios:
            scene_id = scenario.scene_id
            script_file = self.project.script_dir / f"{scene_id}_script.json"

            if not script_file.exists():
                print(f"Script {scene_id}: Writing the script for '{scenario.title}' ...")
                original_scene = scene_by_id.get(scene_id)
                scene_summary = original_scene.scene_summary if original_scene else ""
                if not scene_summary:
                    print(f"[WARN] Scene {scene_id}: scene_summary が見つかりませんでした。空文字で続行します。")
                try:
                    script = self._create_script_sequential(scenario, scene_summary)
                    scripts.append(script)
                except Exception as e:
                    print(f"Error at Script for Scene {scene_id}: {e}")
                    continue
            else:
                print(f"Script '{scene_id}' has already been created. Loading from file...")
                data = self.load_json(script_file)
                scripts.append(Script(**data))

        self.scripts = scripts
        return self.scripts

    def _create_scenario_sequential(self, scene: SceneDesign) -> Scenario:
        print(f"Writing scenario for Scene {scene.scene_id}: {scene.title}...")

        duration_seconds = scene.duration or 60
        target_length = max(350, round(duration_seconds / 60 * 350))

        context = (
            "あなたは経験豊富なメイン・シナリオライターです。シーン設計書とプロットを統合し、"
            "役者が演じるための詳細なシナリオ（トリートメント）を作成します。\n\n"
            f"【シーンタイトル】{scene.title}\n"
            f"【場所（このシーンで扱う唯一のスポット）】{scene.location}\n"
            f"【想定時間】{duration_seconds}秒\n"
            f"【スポット情報（このシーンの舞台に関する史実・具体情報）】\n{scene.facts}\n\n"
            f"【シーン概要】\n{scene.scene_summary}\n\n"
            f"【雰囲気】{scene.atmosphere}\n"
            f"【会話トーン】{scene.narrative_tone}\n"
            f"【空間演出上の留意点】{scene.spatial_direction}\n\n"
            f"【プロタゴニスト】\n{self._describe_character(self.protagonist)}\n\n"
            f"【デュオタゴニスト】\n{self._describe_character(self.deuteragonist)}\n\n"
            "【重要】上記2名それぞれの性別設定と矛盾する代名詞（彼/彼女等）や性別を示す表現を、"
            "物語全体を通して絶対に使用しないでください。\n"
            f"【重要】このシーンの舞台は『{scene.location}』のみです。上記のスポット情報に"
            "記載されていない、他の実在する建物・スポット名（例：別のシーンに登場する史跡など）"
            "を勝手に登場させないでください。場所を混同すると、シナリオ全体が矛盾したものに"
            "なります。\n"
        )
        conversation_history = [{"role": "system", "content": context}]

        question = (
            f"以下は、このシーンの舞台『{scene.location}』に関するスポット情報（史実・具体情報）"
            f"と、このシーンの概要です。この内容を根拠として、このシーンの詳細なシナリオ"
            f"（トリートメント）を執筆してください。\n\n"
            f"--- スポット情報 ---\n{scene.facts}\n--- ここまで ---\n\n"
            f"--- シーン概要 ---\n{scene.scene_summary}\n--- ここまで ---\n\n"
            f"- 上記のスポット情報に記載された具体的な史実・固有名詞（年号・人物名など）を、"
            f"本文の中で実際に活用してください。\n"
            f"- 舞台は『{scene.location}』であることを、本文中で明確に分かるように描写して"
            "ください。\n"
            "- シーン概要にある出来事や関係性を、キャラクターがその場で発見し、"
            "反応する対象として描写してください。\n"
            "- セリフの裏側にあるキャラクターの葛藤や、認知の歪みによる誤解を、ト書きレベルで"
            "精緻に記述してください。\n"
            "- 導入、メイン、オチという流れで書いてください。\n"
            "- まだ「セリフ：〜」という台本形式は取らず、小説のような散文形式で執筆してください。\n"
            "- 挨拶や前置き、見出し記号は一切不要です。本文のみを出力してください。\n"
            f"（{target_length}字程度）"
        )
        scenario_text = self._ask_sequential(conversation_history, question, min_length=50)

        scenario = Scenario(
            scene_id=scene.scene_id,
            title=scene.title,
            character_count=len(scenario_text),
            scenario_text=scenario_text,
        )

        scenario_file = self.project.scenario_dir / f"{scene.scene_id}_scenario.json"
        scenario.save_json(scenario_file)
        return scenario

    def _parse_dialogue_line(self, raw_answer: str, speaker: str) -> Dialogue:
        text = raw_answer.strip()
        instruct = None

        text_match = re.search(r"セリフ[：:]\s*(.+)", raw_answer)
        instruct_match = re.search(r"トーン[：:]\s*(.+)", raw_answer)

        if text_match:
            text = text_match.group(1).strip()
        if instruct_match:
            instruct = instruct_match.group(1).strip()

        # ト書き・地の文が紛れ込んでいないか最低限のクリーニング
        text = text.strip().strip('「」"\'')
        text = text.split("\n")[0].strip()

        return Dialogue(character=speaker, text=text, instruct=instruct)

    def _create_script_sequential(self, scenario: Scenario, scene_summary: str = "") -> Script:
        print(f"Writing script for Scene {scenario.scene_id}: {scenario.title}...")

        protagonist_name = self.protagonist.profile.name
        deuteragonist_name = self.deuteragonist.profile.name
        target_length = scenario.character_count or 1000

        context = (
            "あなたは、詳細なシナリオを、最高にキレのある音声ドラマ台本へと昇華させる劇作家です。\n"
            "文字情報の密度を落とさず、キャラクターの『声』だけでその場の情景とドラマを再現します。\n\n"
            f"【シーンタイトル】{scenario.title}\n"
            f"【シーン概要】\n{scene_summary}\n\n"
            f"【登場人物1：{protagonist_name}】\n{self._describe_character(self.protagonist)}\n\n"
            f"【登場人物2：{deuteragonist_name}】\n{self._describe_character(self.deuteragonist)}\n\n"
        )
        if self.rubi_map:
            context += f"【ルビ辞書（難読語・固有名詞の読み方）】\n{self.rubi_map}\n\n"

        conversation_history = [{"role": "system", "content": context}]

        common_constraints = (
            "\n\n【制約条件】\n"
            "- 発話（セリフ）として音声化される言葉のみを出力してください。\n"
            "- ト書き、ナレーション、SE（効果音指示）、括弧書き（心理描写等）は一切禁止です。\n"
            "- 前置きや解説は不要です。以下の形式のみで出力してください：\n"
            "  セリフ: （ここにセリフ本文）\n"
            "  トーン: （話者のトーンやテンポ、感情強度の指示）\n"
            "- 直前までの発話を言い換えたり、同じ説明を繰り返したりしないでください。常に新しい"
            "情報や感情の進展を提示してください。\n"
            "- 指示語（「それ」「あれ」等）を避け、具体的な固有名詞を使ってください。\n"
        )


        body = []
        speakers = [protagonist_name, deuteragonist_name]
        total_chars = 0
        turn = 0
        max_turns = 60  # 無限ループ防止の安全上限

        scenario_block = (
            f"以下は、このシーンのシナリオ（トリートメント）です。台本は、必ずこの内容に"
            f"忠実に、逸脱しない範囲で執筆してください。\n\n"
            f"--- シナリオ ---\n{scenario.scenario_text}\n--- ここまで ---\n\n"
        )

        while total_chars < target_length and turn < max_turns:
            speaker = speakers[turn % 2]

            if turn == 0:
                question = (
                    f"{scenario_block}"
                    f"このシナリオの導入部分から、{speaker}の最初の一言を書いてください。"
                )
            elif total_chars >= target_length * 0.85:
                question = (
                    f"{scenario_block}"
                    f"シナリオの結末（オチ）に向けて、会話をまとめに入ってください。"
                    f"次は{speaker}の発話です。"
                )
            else:
                question = (
                    f"{scenario_block}"
                    f"上記のシナリオの流れに沿って、会話を続けてください。次は{speaker}の発話です。"
                )

            answer = self._ask_sequential(conversation_history, question, "", common_constraints, min_length=2)
            dialogue = self._parse_dialogue_line(answer, speaker)

            if dialogue.text:
                body.append(dialogue)
                total_chars += len(dialogue.text)

            turn += 1

        script = Script(
            scene_id=scenario.scene_id,
            title=scenario.title,
            character_count=total_chars,
            body=body,
        )

        script_file = self.project.script_dir / f"{scenario.scene_id}_script.json"
        script.save_json(script_file)
        return script