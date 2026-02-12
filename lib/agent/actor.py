# lib/agent/architect.py
import os
from pathlib import Path

from traitlets import Enum

from lib.agent.writer import WriterAgent
from lib.genai.generators import GcpSoundGenerator, QwenSoundGenerator, SoundGenerator
from lib.genai.qwen_tts_local import ATTENTION_TYPE, Qwen3TTS
from lib.schema.script import Script

from .base_agent import BaseAgent
from ..schema.agenda import Agenda
from ..schema.character import CharacterResponse, Character
from ..utils.propmpt_utils import PromptType, PromptLoader
from ..core.project import Project

class VoiceBase(Enum):
    """
    すべての音声列挙型の基底クラス。
    共通のプロパティとフィルタリングロジックを提供します。
    """
    def __init__(self, api_name: str, description: str, gender: str):
        self.api_name = api_name
        self.description = description
        self.gender = gender

    @classmethod
    def get_female_voices(cls):
        return [member for member in cls if member.gender == 'F']

    @classmethod
    def get_male_voices(cls):
        return [member for member in cls if member.gender == 'M']

class GeminiVoice(VoiceBase):
    # Enumメンバー名 = (API名, 特徴, 性別)
    ACHERNAR = ("Achernar", "Soft", "F")
    ACHIRD = ("Achird", "Friendly", "M")
    ALGENIB = ("Algenib", "Gravelly", "M")
    ALGIEBA = ("Algieba", "Smooth", "M")
    ALNILAM = ("Alnilam", "Firm", "M")
    AOEDE = ("Aoede", "Breezy", "F")
    AUTONOE = ("Autonoe", "Bright", "F")
    CALLIRRHOE = ("Callirrhoe", "Easy-going", "F")
    CHARON = ("Charon", "Informative", "M")
    DESPINA = ("Despina", "Smooth", "F")
    ENCELADUS = ("Enceladus", "Breathy", "M")
    ERINOME = ("Erinome", "Clear", "F")
    FENRIR = ("Fenrir", "Excitable", "M")
    GACRUX = ("Gacrux", "Mature", "F")
    IAPETUS = ("Iapetus", "Clear", "M")
    KORE = ("Kore", "Firm", "F")
    LAOMEDEIA = ("Laomedeia", "Upbeat", "F")
    LEDA = ("Leda", "Youthful", "F")
    ORUS = ("Orus", "Firm", "M")
    PUCK = ("Puck", "Upbeat", "M")
    PULCHERRIMA = ("Pulcherrima", "Forward", "M")
    RASALGETHI = ("Rasalgethi", "Informative", "M")
    SADACHBIA = ("Sadachbia", "Lively", "M")
    SADALTAGER = ("Sadaltager", "Knowledgeable", "M")
    SCHEDAR = ("Schedar", "Even", "M")
    SULAFAT = ("Sulafat", "Warm", "F")
    UMBRIEL = ("Umbriel", "Easy-going", "M")
    VINDEMIATRIX = ("Vindemiatrix", "Gentle", "F")
    ZEPHYR = ("Zephyr", "Bright", "F")
    ZUBENELGENUBI = ("Zubenelgenubi", "Casual", "M")

class GcpVoice(VoiceBase):
    # Enumメンバー名 = (API名, 特徴, 性別)
    Achernar = ("ja-JP-Chirp3-HD-Achernar", "Soft", "F")
    Achird = ("ja-JP-Chirp3-HD-Achird", "Friendly", "M")
    Algenib = ("ja-JP-Chirp3-HD-Algenib", "Gravelly", "M")
    Algieba = ("ja-JP-Chirp3-HD-Algieba", "Smooth", "M")
    Alnilam = ("ja-JP-Chirp3-HD-Alnilam", "Firm", "M")
    Aoede = ("ja-JP-Chirp3-HD-Aoede", "Breezy", "F")
    Autonoe = ("ja-JP-Chirp3-HD-Autonoe", "Bright", "F")
    Callirrhoe = ("ja-JP-Chirp3-HD-Callirrhoe", "Easy-going", "F")
    Charon = ("ja-JP-Chirp3-HD-Charon", "Informative", "M")
    Despina = ("ja-JP-Chirp3-HD-Despina", "Smooth", "F")
    Enceladus = ("ja-JP-Chirp3-HD-Enceladus", "Breathy", "M")
    Erinome = ("ja-JP-Chirp3-HD-Erinome", "Clear", "F")
    Fenrir = ("ja-JP-Chirp3-HD-Fenrir", "Excitable", "M")
    Gacrux = ("ja-JP-Chirp3-HD-Gacrux", "Mature", "F")
    Iapetus = ("ja-JP-Chirp3-HD-Iapetus", "Clear", "M")
    Kore = ("ja-JP-Chirp3-HD-Kore", "Firm", "F")
    Laomedeia = ("ja-JP-Chirp3-HD-Laomedeia", "Upbeat", "F")
    Leda = ("ja-JP-Chirp3-HD-Leda", "Youthful", "F")
    Orus = ("ja-JP-Chirp3-HD-Orus", "Firm", "M")
    Puck = ("ja-JP-Chirp3-HD-Puck", "Upbeat", "M")
    Pulcherrima = ("ja-JP-Chirp3-HD-Pulcherrima", "Forward", "F")
    Rasalgethi = ("ja-JP-Chirp3-HD-Rasalgethi", "Informative", "M")
    Sadachbia = ("ja-JP-Chirp3-HD-Sadachbia", "Lively", "M")
    Sadaltager = ("ja-JP-Chirp3-HD-Sadaltager", "Knowledgeable", "M")
    Schedar = ("ja-JP-Chirp3-HD-Schedar", "Even", "M")
    Sulafat = ("ja-JP-Chirp3-HD-Sulafat", "Warm", "F")
    Umbriel = ("ja-JP-Chirp3-HD-Umbriel", "Easy-going", "M")
    Vindemiatrix = ("ja-JP-Chirp3-HD-Vindemiatrix", "Gentle", "F")
    Zephyr = ("ja-JP-Chirp3-HD-Zephyr", "Bright", "F")
    Zubenelgenubi = ("ja-JP-Chirp3-HD-Zubenelgenubi", "Casual", "M")
    Neural2-B = ("ja-JP-Neural2-B", "No Information", "F")
    Neural2-C = ("ja-JP-Neural2-C", "No Information", "M")
    Neural2-D = ("ja-JP-Neural2-D", "No Information", "M")
    Standard-A = ("ja-JP-Standard-A", "No Information", "F")
    Standard-B = ("ja-JP-Standard-B", "No Information", "F")
    Standard-C = ("ja-JP-Standard-C", "No Information", "M")
    Standard-D = ("ja-JP-Standard-D", "No Information", "M")
    Wavenet-A = ("ja-JP-Wavenet-A", "No Information", "F")
    Wavenet-B = ("ja-JP-Wavenet-B", "No Information", "F")
    Wavenet-C = ("ja-JP-Wavenet-C", "No Information", "M")
    Wavenet-D = ("ja-JP-Wavenet-D", "No Information", "M")

class QwenVoice(VoiceBase):
    # ここにQwen3-TTS固有のボイスを定義
    VIVIAN = ("Vivian", "ハイテンション系ボイス。日本語には不向き。", "F")
    RYAN = ("Ryan", "日本語には不向き。", "M")
    SERENA = ("Serena", "日本語には不向き。", "F")
    SOHEE = ("Sohee", "やんデレ系ボイス。ややイントネーションがおかしい。", "F")
    UNCLE_FU = ("Uncle_Fu", "おじさん系ハスキーボイス。ややイントネーションがおかしい。", "M") 
    ERIC = ("Eric", "おっとり系ボイス。ややイントネーションがおかしい。", "M")
    DYLAN = ("Dylan", "ちょっとダウン系青年ボイス。オススメ", "M")
    AIDEN = ("Aiden", "さわやか青年ボイス。オススメ。", "M")
    ONNO_ANNA = ("Onno_Anna", "安定の日本人女性ボイス。オススメ", "F")

class ActorAgent(BaseAgent):
    def __init__(self, 
                 generator: SoundGenerator, 
                 project:Project,
                 character:Character=None,
                 scripts: list[Script]=[],
                 language: str="japanese"
                 ):
        super().__init__(generator)
        self.project = project
        self.character = character
        self.scripts = scripts
        self.language = language

    def generate_monologue(self):
        if isinstance(self.generator, QwenSoundGenerator):
            self._generate_qwen_api()
        elif isinstance(self.generator, GcpSoundGenerator):
            self._generate_gcp_api()
        else:
            self._generate_qwen_local() 
    def _generate_gcp_api(self):
        pass

    def _generate_qwen_api(self):
        for script in self.scripts:
            base_name = str(script.scene_id) + "_" + script.title
            output_file = self.project.drama_dir / f"{base_name}.wav"
            if not os.path.exists(output_file):
                monologues = None
                speakers = None
                intructs = None
                
                for monologue in script.body:
                    monologues.append(monologue.text)
                    intructs.append(monologue.instruct)
                    speakers.append(self.character.profile.voice)
                
                # --- 言語リストの作成は、全てのセリフ（monologues）を溜めた後に実行 ---
                if isinstance(self.language, str):
                    language_list = [self.language] * len(monologues)
                else:
                    language_list = self.language

                # 音声合成（API経由でサーバーへリクエスト）
                result = self.voice_generator.generate(
                    output_path=output_file,
                    texts=monologues,
                    languages=language_list,
                    speakers=speakers,
                    instructs=intructs
                )

                # 返り値が None なら、その時点で処理を止める（サーバーが死んでいる証拠）
                if result is None:
                    print(f"ERROR: Sound generation failed for {output_file}. Stopping further processing.")
                    break

                print(f"Sound file generated: {output_file}")
            else:
                print(f"Sound file already exists: {output_file}")

    def _generate_qwen_local(self):
        # モデル初期化
        tts_model = Qwen3TTS(
            model_name="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            device="cuda:0",
            attention_type=ATTENTION_TYPE.SDPA
        )

        # 各ファイルを処理
        for script in self.scripts:
            # 出力ファイル名を決定（例：1_audio.wav）
            base_name = script.scene_id + script.title
            output_file = self.project.drama_dir / f"{base_name}.wav"

            if not os.path.exists(output_file):
                # スクリプトデータの抽出
                monologues = None
                speakers = None
                intructs = None
                for monologue in script.body:
                    monologues.append(monologue.text)
                    intructs.append(monologue.instruct)

                    if monologue.character == self.protagonist.profile.name:
                        speakers.append(self.protagonist.profile.voice)
                    elif monologue.character == self.duotagonist.profile.name:
                        speakers.append(self.duotagonist.profile.voice)
                    else:
                        speakers.append("default")
                    
                    if isinstance(self.language, str):
                        language_list = [self.language] * len(script.body)
                    else:
                        language_list = self.language

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

class DialogueAgent(BaseAgent):
    def __init__(
            self, 
            generator: SoundGenerator, 
            project:Project, 
            agenda:Agenda,
            scripts: list[Script], 
            protagonist:Character, 
            duotagonist:Character, 
            language: str="japanese"
    ):
        super().__init__(generator)
        self.project = project
        self.agenda = agenda
        self.scripts = scripts
        self.protagonist = protagonist
        self.duotagonist = duotagonist
        self.language = language

    def generate_dialogues(self):
        if isinstance(self.generator, QwenSoundGenerator):
            self._generate_qwen_api()
        elif isinstance(self.generator, GcpSoundGenerator):
            self._generate_gcp_api()
        else:
            self._generate_qwen_local() 
    
    def _generate_gcp_api(self):
        pass

    def _generate_qwen_api(self):
        for script in self.scripts:
            base_name = str(script.scene_id) + "_" + script.title
            output_file = self.project.drama_dir / f"{base_name}.wav"
            if not os.path.exists(output_file):
                dialogues = None
                speakers = None
                intructs = None
                
                for dialogue in script.body:
                    dialogues.append(dialogue.text)
                    intructs.append(dialogue.instruct)

                    if dialogue.character == self.protagonist.profile.name:
                        speakers.append(self.protagonist.profile.voice)
                    elif dialogue.character == self.duotagonist.profile.name:
                        speakers.append(self.duotagonist.profile.voice)
                    else:
                        speakers.append("default")
                
                # --- 言語リストの作成は、全てのセリフ（dialogues）を溜めた後に実行 ---
                if isinstance(self.language, str):
                    language_list = [self.language] * len(dialogues)
                else:
                    language_list = self.language

                # 音声合成（API経由でサーバーへリクエスト）
                result = self.voice_generator.generate(
                    output_path=output_file,
                    texts=dialogues,
                    languages=language_list,
                    speakers=speakers,
                    instructs=intructs
                )

                # 返り値が None なら、その時点で処理を止める（サーバーが死んでいる証拠）
                if result is None:
                    print(f"ERROR: Sound generation failed for {output_file}. Stopping further processing.")
                    break

                print(f"Sound file generated: {output_file}")
            else:
                print(f"Sound file already exists: {output_file}")

    def _generate_qwen_local(self):
        # モデル初期化
        tts_model = Qwen3TTS(
            model_name="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            device="cuda:0",
            attention_type=ATTENTION_TYPE.SDPA
        )

        # 各ファイルを処理
        for script in self.scripts:
            # 出力ファイル名を決定（例：1_audio.wav）
            base_name = script.scene_id + script.title
            output_file = self.project.drama_dir / f"{base_name}.wav"

            if not os.path.exists(output_file):
                # スクリプトデータの抽出
                dialogues = None
                speakers = None
                intructs = None
                for dialogue in script.body:
                    dialogues.append(dialogue.text)
                    intructs.append(dialogue.instruct)

                    if dialogue.character == self.protagonist.profile.name:
                        speakers.append(self.protagonist.profile.voice)
                    elif dialogue.character == self.duotagonist.profile.name:
                        speakers.append(self.duotagonist.profile.voice)
                    else:
                        speakers.append("default")
                    
                    if isinstance(self.language, str):
                        language_list = [self.language] * len(script.body)
                    else:
                        language_list = self.language

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