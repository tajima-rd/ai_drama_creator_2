# lib/agent/base_agent.py

from dataclasses import Field
import time
import re
import json

import pydantic
from pydantic_core import ValidationError

from pathlib import Path
from typing import Type, TypeVar, Dict, Any, Optional

from ..genai.generators import SoundGenerator, TextGenerator
from ..utils.propmpt_utils import PromptUtils

T = TypeVar("T", bound=pydantic.BaseModel)

def sanitize_json_string(json_str: str) -> str:
    # 制御文字（U+0000〜U+001F）を削除
    sanitized = re.sub(r'[\x00-\x1f]', '', json_str)
    return sanitized


class BaseAgent:
    def __init__(
            self, 
            text_generator: Optional[TextGenerator] = None, 
            voice_generator: Optional[SoundGenerator] = None
        ):
        self.text_generator = text_generator
        self.voice_generator = voice_generator
    
    @staticmethod
    def load_json(file_path: Path) -> Dict[str, Any]:
        """Pathオブジェクトを直接受け取ってロードする"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_json(data: Any, file_path: Path):
        """Pathオブジェクトを直接受け取って保存する"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Pydanticモデルの場合はdictに変換
        output_data = data.model_dump() if hasattr(data, "model_dump") else data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    def _execute(self, prompt_path: Path, variables: Dict[str, Any], response_schema: Type[T], max_retries: int =10) -> T:
        """
        プロンプトの読み込み、変数注入、生成、バリデーションを一括で行う。
        エラーが発生した場合は最大 max_retries 回まで再試行。
        """
        final_prompt = PromptUtils.load_and_format(prompt_path, variables)

        for attempt in range(max_retries):
            try:
                messages = [{"role": "user", "content": final_prompt}]
                raw_json = self.generator.generate(messages)
                sanitized_json = sanitize_json_string(raw_json)

                return response_schema.model_validate_json(sanitized_json)
            except ValidationError as e:
                print(f"[Attempt {attempt + 1}/{max_retries}] Validation Error: {e}")
                if attempt == max_retries - 1:
                    raise  # 最後の試行でも失敗した場合、エラーを投げる
                time.sleep(1)  # 少し待機して再試行
        raise RuntimeError("Unexpected state in _execute")

class SaveableModel(pydantic.BaseModel):
    def save_json(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.model_dump_json(indent=2))