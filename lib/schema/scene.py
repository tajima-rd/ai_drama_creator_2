from typing import Literal, Optional, Dict
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class SceneDesign(SaveableModel):
    scene_id: Optional[int] = Field(None, description="ソート用の番号")
    title: Optional[str] = Field(None, description="シーン設計案（仮タイトル）")
    location: Optional[str] = Field(None, description="舞台となる場所の名称")
    duration: Optional[int] = Field(None, description="シーンの時間（分）")
    scene_plot: Optional[str] = Field(None, description="シーンのプロット案")
    scene_summary: Optional[str] = Field(None, description="シーンの概要")
    facts: Optional[str] = Field(None, description="場所の基礎情報（歴史・文化・自然など）")
    instruction: Optional[str] = Field(None, description="シーンに関する指示事項")
    atmosphere: Optional[str] = Field(None, description="現場の雰囲気・空気感")
    narrative_tone: Optional[str] = Field(None, description="登場人物の声のトーン")
    spatial_direction: Optional[str] = Field(None, description="空間演出上の留意点")

SceneDesignResponse = BaseResponse[SceneDesign]
