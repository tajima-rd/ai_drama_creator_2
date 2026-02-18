from typing import Literal, Optional
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Review(SaveableModel):
    Judgement: str = Field(..., description="合格、要修正のいずれかで回答")
    comments: Optional[str] = Field(None, description="レビューコメント")
    requirements: Optional[str] = Field(None, description="要修正の場合の修正要件")

ReviewResponse = BaseResponse[Review]