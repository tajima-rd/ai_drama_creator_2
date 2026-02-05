from typing import Literal, Optional, Dict
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class RegionSummary(SaveableModel):
    title: str = Field(..., description="地域の特徴を表すタイトル（仮タイトル）")
    summary: str = Field(..., description="舞台となる場所の概要")
    features: str = Field(..., description="舞台となる場所の特徴（自然系、歴史系、娯楽系などの系統を軸に説明）")

RegionSummaryResponse = BaseResponse[RegionSummary]
