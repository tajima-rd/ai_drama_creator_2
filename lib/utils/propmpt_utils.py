import re
from pathlib import Path
from typing import Dict, Any
from enum import Enum

class PromptType(Enum):
    CREATE_AGENDA = "create_agenda.txt"
    CREATE_CHARACTER = "create_character.txt"
    CREATE_PLOT = "create_plot.txt"
    CREATE_REPORT = "create_report.txt"
    CREATE_SCRIPT = "create_script.txt"
    CREATE_SCENE = "create_scene.txt"
    

class PromptUtils:
    @staticmethod
    def get_path(base_dir: Path, prompt_type: PromptType) -> Path:
        return base_dir / prompt_type.value

    @staticmethod
    def load_and_format(prompt_path: Path, variables: Dict[str, Any]) -> str:
        """
        プロンプトファイルを読み込み、指定された変数を埋め込む。
        """
        if not prompt_path.exists():
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_path}")
            
        content = prompt_path.read_text(encoding="utf-8")
        
        # 変数置換 (例: {{variable_name}} を置換)
        return PromptUtils.format_prompt(content, variables)

    @staticmethod
    def format_prompt(content: str, variables: Dict[str, Any]) -> str:
        """
        文字列内の {{variable}} を variables 辞書の内容で置換する。
        """
        formatted_content = content
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            formatted_content = formatted_content.replace(placeholder, str(value))
            
        # 埋め込まれなかった変数が残っている場合の警告や処理をここに追加可能
        return formatted_content.strip()