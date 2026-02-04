from typing import Literal, Optional
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class PlotDesign(SaveableModel):
    title: str = Field(..., description="物語のタイトル")
    synopsis: str = Field(..., description="あらすじ（800字〜1200字程度：導入・出会い・転機・余韻を含む構成）")
    emotional_arc: str = Field(..., description="物語を通じた主人公の感情変化のプロセス")
    narrative_integration: str = Field(..., description="地域資源（シーズ）やニーズをどのように物語へ織り込んだかの解説")

PlotResponse = BaseResponse[PlotDesign]
