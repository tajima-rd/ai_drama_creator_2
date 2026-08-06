from typing import Literal, Optional, Dict
from pydantic import BaseModel, Field

from ..agent.base_agent import SaveableModel
from .response import BaseResponse

class SceneDesign(SaveableModel):
    scene_id: Optional[int] = Field(None, description="ソート用の番号")
    location: Optional[str] = Field(None, description="舞台となる場所の名称")
    duration: Optional[int] = Field(None, description="シーンの時間（分）")
    scene_plot: Optional[str] = Field(None, description="シーンのプロット案")
    facts: Optional[str] = Field(None, description="場所の基礎情報（歴史・文化・自然など）")
    instruction: Optional[str] = Field(None, description="シーンに関する指示事項")
    # 以下5つは create_scene.txt の Output Schema に含まれる、AIの応答
    # から直接得られるべきフィールド。以前は Optional だったため、
    # モデルが別のキー名（"summary" 等）で応答した場合でも None のまま
    # 静かに通過してしまっていた。必須化することで、キー名の不一致を
    # ValidationError として確実に検知できるようにする。
    # ※ setup_scenes() での初期構築時には、director.py 側で
    #   空文字 "" を明示的に渡すよう対応済み。
    title: str = Field(..., description="シーン設計案（仮タイトル）")
    scene_summary: str = Field(..., description="シーンの概要")
    atmosphere: str = Field(..., description="現場の雰囲気・空気感")
    narrative_tone: str = Field(..., description="登場人物の声のトーン")
    spatial_direction: str = Field(..., description="空間演出上の留意点")

SceneDesignResponse = BaseResponse[SceneDesign]