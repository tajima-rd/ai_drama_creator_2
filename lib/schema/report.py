from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Report(SaveableModel):
    # geography.py の RegionSummary と同様、AIの応答からのみ生成される
    # オブジェクトのため、必須化しても安全。
    title: str = Field(..., description="レポートタイトル")
    background: str = Field(..., description="調査背景")
    tourist_data_summary: str = Field(..., description="データの要約")
    potential_needs: str = Field(..., description="潜在ニーズ")
    potential_seeds: str = Field(..., description="潜在シーズ")
    target_layer: str = Field(..., description="ターゲット層")

ReportResponse = BaseResponse[Report]