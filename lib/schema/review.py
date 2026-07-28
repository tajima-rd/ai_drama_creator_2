from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Review(SaveableModel):
    Judgement: str = Field(..., description="合格、要修正のいずれかで回答")
    comments: Optional[str] = Field(None, description="レビューコメント")
    requirements: Optional[List[str]] = Field(None, description="要修正の場合の修正要件（箇条書き）")

    @field_validator("requirements", mode="before")
    @classmethod
    def _coerce_requirements(cls, v):
        # モデルが単一の文字列で返してきた場合もリストとして受け入れる
        if isinstance(v, str):
            return [v]
        return v

ReviewResponse = BaseResponse[Review]