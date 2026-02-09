from typing import Literal, Optional, Dict
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class SceneDesign(SaveableModel):
    scene_id: int = Field(..., description="ソート用の番号")
    title: str = Field(..., description="シーン設計案（仮タイトル）")
    location: str = Field(..., description="舞台となる場所の名称")
    scene_summary: str = Field(..., description="シーンの概要")
    facts: str = Field(..., description="場所の基礎情報（歴史・文化・自然など）")
    atmosphere: str = Field(..., description="現場の雰囲気・空気感")
    narrative_tone: str = Field(..., description="登場人物の声のトーン")
    spatial_direction: str = Field(..., description="空間演出上の留意点")

SceneDesignResponse = BaseResponse[SceneDesign]
