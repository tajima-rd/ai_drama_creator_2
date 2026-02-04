from typing import Literal, Optional
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Agenda(SaveableModel):
    title: str = Field(..., description="ストーリーの核となるテーマを明確に表現したタイトル")
    overview: str = Field(..., description="概要 (400字程度)")
    needs: str = Field(..., description="潜在ニーズ (400字程度)")
    seeds: str = Field(..., description="潜在シーズ (400字程度)")
    planning: str = Field(..., description="企画内容 (400字程度)")
    concept: str = Field(..., description="ストーリー概念 (400字程度)")

AgendaResponse = BaseResponse[Agenda]
