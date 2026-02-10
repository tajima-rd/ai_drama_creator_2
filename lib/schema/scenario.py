import re

from typing import List, Literal, Optional
from pydantic import field_validator, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Scenario(SaveableModel):
    """台本生成のメイン構造"""
    scene_id: Optional[int] = Field(None, description="シーンID")
    title: Optional[str] = Field(None, description="シーンタイトル")
    character_count: Optional[int]  = Field(None, description="総文字数（Total: ○○文字）")
    scenario_text: Optional[str] = Field(None, description="詳細なシナリオ文章（ト書きと感情描写、会話の骨子を含む")

ScenarioResponse = BaseResponse[Scenario]
