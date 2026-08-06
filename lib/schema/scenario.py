import re

from typing import List, Literal, Optional
from pydantic import field_validator, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class Scenario(SaveableModel):
    """台本生成のメイン構造"""
    scene_id: Optional[int] = Field(None, description="シーンID")
    title: Optional[str] = Field(None, description="シーンタイトル")
    # scenario_text / character_count は必ずモデルの応答に含まれるべき
    # 必須フィールド。以前は Optional にしていたため、モデルが
    # "scenario_text" の代わりに "text" 等の別名キーで応答した場合でも
    # バリデーションエラーにならず、値が None のまま静かに保存されて
    # しまう不具合があった。必須化することで、キー名の不一致が
    # 確実に ValidationError として検知され、既存のリトライ機構が
    # 正しく働くようにする。
    character_count: int = Field(..., description="総文字数（Total: ○○文字）")
    scenario_text: str = Field(..., description="詳細なシナリオ文章（ト書きと感情描写、会話の骨子を含む")

ScenarioResponse = BaseResponse[Scenario]