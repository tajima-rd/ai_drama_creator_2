from typing import Literal, Optional, Dict
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class RegionSummary(SaveableModel):
    # AIの応答からのみ生成されるオブジェクトのため、必須化しても
    # 他の箇所（部分的な事前構築）に影響しない。以前は Optional で
    # あったため、モデルがキー名を間違えても静かに None のまま
    # 通ってしまう問題があったため、必須化してリトライが正しく
    # 働くようにする。
    title: str = Field(..., description="地域の特徴を表すタイトル（仮タイトル）")
    summary: str = Field(..., description="舞台となる場所の概要")
    features: str = Field(..., description="舞台となる場所の特徴（自然系、歴史系、娯楽系などの系統を軸に説明）")


RegionSummaryResponse = BaseResponse[RegionSummary]