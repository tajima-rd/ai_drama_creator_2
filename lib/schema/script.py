from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Dialogue(SaveableModel):
    """1発話ごとのデータ構造"""
    character: str = Field(..., description="発話するキャラクター名")
    dialogue: str = Field(..., description="台詞内容（ト書き・記号一切禁止）")
    instruct: Optional[str] = Field(None, description="話者トーンやテンポ、感情強度の指示")

class Script(SaveableModel):
    """台本生成のメイン構造"""
    scene_id: Optional[int] = Field(None, description="シーンID")
    title: Optional[str] = Field(None, description="シーンタイトル")
    character_count: Optional[int] = Field(None, description="総文字数（Total:）")
    duration: Optional[int] = Field(None, description="想定尺（分・秒）")
    body: List[Dialogue] = Field(..., description="交互発話のリスト")

ScriptResponse = BaseResponse[Script]
