from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Report(SaveableModel):
    title: Optional[str] = Field(None, description="レポートタイトル")
    background: Optional[str] = Field(None, description="調査背景")
    tourist_data_summary: Optional[str] = Field(None, description="データの要約")
    potential_needs: Optional[str] = Field(None, description="潜在ニーズ")
    potential_seeds: Optional[str] = Field(None, description="潜在シーズ")
    target_layer: Optional[str] = Field(None, description="ターゲット層")

ReportResponse = BaseResponse[Report]
