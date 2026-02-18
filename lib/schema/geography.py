from typing import Literal, Optional, Dict
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class RegionSummary(SaveableModel):
    # 初期化時はすべて None になるように変更
    title: Optional[str] = Field(None, description="地域の特徴を表すタイトル（仮タイトル）")
    summary: Optional[str] = Field(None, description="舞台となる場所の概要")
    features: Optional[str] = Field(None, description="舞台となる場所の特徴（自然系、歴史系、娯楽系などの系統を軸に説明）")


RegionSummaryResponse = BaseResponse[RegionSummary]
