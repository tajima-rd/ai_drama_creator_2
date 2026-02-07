import re

from typing import List, Literal, Optional
from pydantic import field_validator, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Scenario(SaveableModel):
    """台本生成のメイン構造"""
    scene_id: str = Field(..., description="シーンID")
    scene_title: str = Field(..., description="シーンタイトル")
    character_count: str = Field(..., description="総文字数（Total: ○○文字）")
    scenario_text: str = Field(..., description="2000字程度の詳細なシナリオ文章（ト書きと感情描写、会話の骨子を含む")

    @field_validator("scene_id")
    @classmethod
    def validate_scene_id(cls, v: str) -> str:
        # SCN- + 数字3桁 以外を弾く
        if not re.fullmatch(r"SCN-\d{3}", v):
            raise ValueError(f"シーンIDのフォーマットが不正です(SCN-001形式が必要): {v}")
        return v

ScenarioResponse = BaseResponse[Scenario]
