# lib/agent/base_agent.py

import time
import re
import json
import pydantic

from pathlib import Path
from typing import (
    List, 
    TypeVar, 
    Dict, 
    Any, 
    Optional
)
from ..genai import (
    SoundGenerator, 
    TextGenerator
)

T = TypeVar("T", bound=pydantic.BaseModel)

def clean_speech(text: str) -> str:
    # 改行以降をカット（もしAIが補足説明を書いた場合）
    text = text.split('\n')[0]
    # 典型的な前置きを削除（正規表現等で）
    text = re.sub(r'^.*?は「?|」?です。?$', '', text)
    return text.strip(' 「」"\'')

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
        
        return raw_text.strip()

    @staticmethod
    def _describe_character(character) -> str:
        p = character.profile
        return (
            f"名前: {p.name}\n"
            f"年齢: {p.age} / 性別: {p.gender}\n"
            f"性格: {p.personality}\n"
            f"話し方: {p.speaking_style}\n"
            f"経歴: {p.background}\n"
            f"認知の歪み（物事をどう誤解するか）: {p.cognitive_bias}\n"
            f"価値観: {p.value_system}\n"
            f"行動様式: {p.action}"
        )

    def _chat_step_with_retry(
        self,
        conversation_history: List[Dict[str, str]],
        max_retries: int = 5,
        min_length: int = 2,
    ) -> str:
        RESTART_AFTER_N_FAILURES = 2
        last_exception: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                text = self._chat_step(conversation_history)

                if not text or len(text.strip()) < min_length:
                    raise ValueError(f"応答が空、または短すぎます（{len(text)}文字）")

                # <unused49> のような予約トークンや、明らかな崩壊パターンの検知
                head = text[:80]
                if "<unused" in head or "<|" in head or "<end_of_turn>" in head:
                    raise ValueError(f"崩壊したトークン列が検出されました: {head!r}")

                return text

            except Exception as e:
                last_exception = e
                print(f"[chat_step Attempt {attempt + 1}/{max_retries}] 失敗: {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"chat_stepが{max_retries}回失敗しました: {last_exception}") from last_exception

                if (attempt + 1) % RESTART_AFTER_N_FAILURES == 0 and hasattr(self.text_generator, "reset_server"):
                    print(f"[chat_step Attempt {attempt + 1}/{max_retries}] 連続失敗のため、LLMサーバーのリセットを試みます...")
                    self.text_generator.reset_server()

                time.sleep(1)

        raise RuntimeError("Unexpected state in _chat_step_with_retry")

    def _ask_sequential(
        self,
        conversation_history: List[Dict[str, str]],
        question: str,
        length_hint: str = "",
        common_constraints: str = "",
        min_length: int = 2,
    ) -> str:
        conversation_history.append({
            "role": "user",
            "content": f"{question}{length_hint}{common_constraints}"
        })
        answer = self._chat_step_with_retry(conversation_history, min_length=min_length)
        conversation_history.append({"role": "assistant", "content": answer})
        print(f"[DEBUG] ask() answer: {answer[:200]!r}")
        return answer

    def _ask_title(
        self,
        conversation_history: List[Dict[str, str]],
        question: str,
        common_constraints: str = "",
    ) -> str:
        title = self._ask_sequential(
            conversation_history,
            question,
            "（タイトルのみを1行で。説明や記号は不要）",
            common_constraints,
        )
        return title.strip().split("\n")[0].strip(' 「」"\'')

class SaveableModel(pydantic.BaseModel):
    def save_json(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.model_dump_json(indent=2))