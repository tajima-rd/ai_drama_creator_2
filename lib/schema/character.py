from typing import Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Profile(SaveableModel):
    # 以下は create_character.txt の Output Schema でAIに必ず生成させて
    # いる主要フィールド。以前は Optional だったため、モデルがキー名を
    # 間違えても None のまま静かに通過してしまっていた。必須化することで
    # ValidationError として確実に検知できるようにする。
    # ※ ArchitectAgent.__init__ での初期構築時には、空文字 "" を
    #   明示的に渡すよう対応済み。
    name: str = Field(..., description="氏名：(ニックネームや不明なども可)")
    bond: str = Field(..., description="相方（protagonist / deuteragonist）との関係性")
    age: str = Field(..., description="年齢：(不詳なども可)")
    gender: str = Field(..., description="性別：(不詳なども可)")
    personality: str = Field(..., description="性格：(不詳なども可)")
    speaking_style: str = Field(..., description="話し方")
    background: str = Field(..., description="経歴")
    knowledge: str = Field(..., description="知識")
    experience: str = Field(..., description="経験：誕生から現在までを詳細に作成")
    cognitive_bias: str = Field(..., description="事実を独自の知識体系でどう誤解・変換するか")
    value_system: str = Field(..., description="何を良しとし、何を嫌うか。")
    action: str = Field(..., description="キャラクターの行動（舞台の中での具体的な行動様式）")
    # 以下は実データ上も null が正常値として使われているため、
    # 引き続き Optional のままにする。
    catchphrase: Optional[str] = Field(None, description="口癖")
    text_example: Optional[str] = Field(None, description="実際のセリフの数行の例。")
    relationships: Optional[str] = Field(None, description="人間関係")

class Character(SaveableModel):
    role_type: Literal["protagonist", "deuteragonist"]
    profile: Profile
    voice: Optional[str] = Field(None, description="アサインされた話者。自動選定ロジックで使用")

CharacterResponse = BaseResponse[Character]