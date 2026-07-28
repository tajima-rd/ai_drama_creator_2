# lib/agent/base_agent.py

from dataclasses import Field
import time
import re
import json

import pydantic
from pydantic_core import ValidationError

from pathlib import Path
from typing import List, Type, TypeVar, Dict, Any, Optional

from ..genai.generators import SoundGenerator, TextGenerator
from ..utils.propmpt_utils import PromptLoader

T = TypeVar("T", bound=pydantic.BaseModel)

def clean_speech(text: str) -> str:
    # 改行以降をカット（もしAIが補足説明を書いた場合）
    text = text.split('\n')[0]
    # 典型的な前置きを削除（正規表現等で）
    text = re.sub(r'^.*?は「?|」?です。?$', '', text)
    return text.strip(' 「」"\'')

def sanitize_json_string(json_str: str) -> str:
    # Remove leading/trailing whitespace.
    json_str = json_str.strip()

    # Convert markdown code blocks to plain JSON if they exist
    start_idx = -1
    for i, char in enumerate(json_str):
        if char in '{[':
            start_idx = i
            break            
    end_idx = -1

    for i, char in enumerate(reversed(json_str)):
        if char in '}]':
            end_idx = len(json_str) - i
            break
    if start_idx != -1 and end_idx != -1:
        json_str = json_str[start_idx:end_idx]

    # Remove any remaining non-printable characters
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
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_json(data: Any, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        output_data = data.model_dump() if hasattr(data, "model_dump") else data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    def _chat_step(self, conversation_history: List[Dict[str, str]]) -> str:
        # response_schemaを使わず、単なる文字列として生成
        raw_text = self.text_generator.generate(conversation_history)
        
        # 最低限のクリーニング（前後の空白除去など）
        return raw_text.strip()

    def _execute(
        self, 
        prompt_path: Path, 
        variables: Dict[str, Any], 
        response_schema: Type[T], 
        max_retries: int = 10,
        retry_on_logical_error: bool = True   # ← 追加
    ) -> T:
        final_prompt = PromptLoader.load_and_format(prompt_path, variables)

        # print(f"[DEBUG] final_prompt length: {len(final_prompt)} chars")
        # print("="*20 + " PROMPT START " + "="*20)
        # print(final_prompt)
        # print("="*20 + " PROMPT END " + "="*20)


        last_error_message = None

        for attempt in range(max_retries):
            try:
                messages = [{"role": "user", "content": final_prompt}]
                raw_json = self.text_generator.generate(messages)

                # print(f"[DEBUG] raw model response:\n{raw_json}")

                sanitized_json = sanitize_json_string(json_str=raw_json)

                parsed = response_schema.model_validate_json(sanitized_json)

                # JSONとしては正しいが、モデルが status:"error" を返してきた場合もリトライする
                if retry_on_logical_error and parsed.status == "error":
                    last_error_message = parsed.message
                    print(f"[Attempt {attempt + 1}/{max_retries}] Model returned status=error: {parsed.message}")
                    if attempt == max_retries - 1:
                        return parsed  # 最終試行なら諦めてそのまま返す（呼び出し元でValueErrorになる）
                    time.sleep(1)
                    continue

                return parsed

            except ValidationError as e:
                print(f"[Attempt {attempt + 1}/{max_retries}] Validation Error: {e}")
                if attempt == max_retries - 1:
                    raise 
                time.sleep(1)  

        raise RuntimeError("Unexpected state in _execute")

class SaveableModel(pydantic.BaseModel):
    def save_json(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.model_dump_json(indent=2))