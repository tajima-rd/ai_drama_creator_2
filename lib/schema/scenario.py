from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Scenario(SaveableModel):
    """台本生成のメイン構造"""
    scene_id: int = Field(..., description="シーンID")
    scene_title: str = Field(..., description="シーンタイトル")
    character_count: str = Field(..., description="総文字数（Total: ○○文字）")
    scenario_text: str = Field(..., description="2000字程度の詳細なシナリオ文章（ト書きと感情描写、会話の骨子を含む")

ScenarioResponse = BaseResponse[Scenario]
