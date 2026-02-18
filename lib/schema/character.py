from typing import Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Profile(SaveableModel):
    name: Optional[str] = Field(None, description="氏名：(ニックネームや不明なども可)")
    bond: Optional[str] = Field(None, description="相方（protagonist / deuteragonist）との関係性")
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
    text_example: Optional[str] = Field(None, description="実際のセリフの数行の例。")
    relationships: Optional[str] = Field(None, description="人間関係")
    action: Optional[str] = Field(None, description="キャラクターの行動（舞台の中での具体的な行動様式）")

class Character(SaveableModel):
    role_type: Literal["protagonist", "deuteragonist"]
    profile: Profile
    voice: Optional[str] = Field(None, description="アサインされた話者。自動選定ロジックで使用")

CharacterResponse = BaseResponse[Character]
