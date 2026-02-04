# response.py
from typing import Literal, Optional, TypeVar, Generic
from pydantic import BaseModel, Field

# 任意のモデルを受け入れるための変数
T = TypeVar("T", bound=BaseModel)

class BaseResponse(BaseModel, Generic[T]):
    """
    システム全体で利用する共通のレスポンスフォーマット
    """
    status: Literal["ready", "error"] = Field(
        ..., 
        description="ステータス（準備完了 'ready' または エラー 'error'）"
    )
    message: str = Field(
        ..., 
        description="準備完了時のメッセージ、または情報不足時の警告内容"
    )
    result: Optional[T] = Field(
        None, 
        description="処理結果の本体。エラー時はNone"
    )