from typing import Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

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

class QwenVoice(VoiceBase):
    # ここにQwen3-TTS固有のボイスを定義
    VIVIAN = ("Vivian", "Vivian", "F")          # ちょっと、ハイテンション系ボイス
    RYAN = ("Ryan", "Ryan", "M")                # ちょっと、日本語のイントネーションがおかしい
    SERENA = ("Serena", "Serena", "F")          # ちょっと、日本語のイントネーションがおかしい
    SOHEE = ("Sohee", "Sohee", "F")             # ▲ やんデレ系ボイス
    UNCLE_FU = ("Uncle_Fu", "Uncle_Fu", "M")    # ▲ おじさん系ハスキーボイス
    ERIC = ("Eric", "Eric", "M")                # ▲ おっとり系ボイス
    DYLAN = ("Dylan", "Dylan", "M")             # ◎ ちょっとダウン系青年ボイス
    AIDEN = ("Aiden", "Aiden", "M")             # ◎ さわやか青年ボイス
    ONNO_ANNA = ("Onno_Anna", "Onno_Anna", "F") # ◎ 安定の日本人女性ボイス

class Profile(SaveableModel):
    name: str = Field(..., description="氏名：(ニックネームや不明なども可)")
    bond: str = Field(..., description="相方（protagonist / duotagonist）との関係性")
    age: Optional[str] = Field(None, description="年齢：(不詳なども可)")
    gender: Optional[str] = Field(None, description="性別：(不詳なども可)") 
    personality: Optional[str] = Field(None, description="性格：(不詳なども可)")
    speaking_style: Optional[str] = Field(None, description="話し方")
    catchphrase: Optional[str] = Field(None, description="口癖")
    background: Optional[str] = Field(None, description="経歴")
    knowledge: Optional[str] = Field(None, description="知識")
    experience: Optional[str] = Field(None, description="経験：誕生から現在までを詳細に作成")
    cognitive_bias: Optional[str] = Field(None, description="事実を独自の知識体系でどう誤解・変換するか")
    value_system: Optional[str] = Field(None, description="何を良しとし、何を嫌うか。")
    dialogue_example: Optional[str] = Field(None, description="実際のセリフの数行の例。")
    relationships: Optional[str] = Field(None, description="人間関係")
    voice: Optional[str] = Field(None, description="アサインされた話者。自動選定ロジックで使用")

class Character(SaveableModel):
    role_type: Literal["protagonist", "duotagonist"]
    profile: Profile

CharacterResponse = BaseResponse[Character]
