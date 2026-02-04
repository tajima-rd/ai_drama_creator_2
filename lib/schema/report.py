from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Report(SaveableModel):
    title: str = Field(..., description="ストーリーの核となるテーマを明確に表現したタイトル")
    background: str = Field(..., description="調査背景（200字程度）")
    tourist_data_summary: str = Field(..., description="観光客データの要約（400字程度）")
    potential_needs: str = Field(..., description="潜在ニーズの分析（400字程度）")
    potential_seeds: str = Field(..., description="潜在シーズの分析（400字程度）")
    target_layer: str = Field(..., description="ターゲット層の分析（400字程度）")

ReportResponse = BaseResponse[Report]
