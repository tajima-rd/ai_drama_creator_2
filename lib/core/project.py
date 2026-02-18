import json
from pathlib import Path
from typing import Optional

class Project:
    def __init__(
        self, 
        project_name: str = "", 
        description: str = "",
        project_dir: Path = None,  # JSON内の "project_dir" を受ける
        gis_data: Path = None,
        rubi_map: Path = None,
        base_path: Path = None,
        llm_client: Optional[str] = "",
        llm_model: Optional[str] = "",
        llm_api: Optional[str] = "",
        tts_client: Optional[str] = "",
        tts_model: Optional[str] = "",
        tts_api: Optional[str] = ""
    ):
        self.project_name = project_name
        self.description = description

        # すべての相対パスを base_path (project.jsonの場所) を起点に絶対パス化
        root = base_path if base_path else Path.cwd()

        project_root = Path(project_dir)
        if project_root.is_absolute():
            self.project_dir = project_root
        else:
            # root と p_dir が同じ名前（例: "project"）なら重複させないロジック
            if root.name == project_root.name:
                self.project_dir = root.resolve()
            else:
                self.project_dir = (root / project_root).resolve()

        self.prompt_dir = (root.parent / "configure" / "prompts").resolve()
        self.secret_dir = (root.parent / "configure" / "secret").resolve()
        self.system_dir = (root.parent / "configure" / "system").resolve()

        self.gis_data = (root.parent / gis_data).resolve()
        self.rubi_map = (root.parent / rubi_map).resolve()

        # 関連ディレクトリの設定
        self.output_dir = self.project_dir / "output"
        self.scene_dir = self.output_dir / "scenes"
        self.scenario_dir = self.output_dir / "scenarios"
        self.script_dir = self.output_dir / "scripts"
        self.drama_dir = self.output_dir / "dramas"

        # LLMの設定
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.llm_api = llm_api

        # TTSの設定
        self.tts_client = tts_client
        self.tts_model = tts_model
        self.tts_api = tts_api

        # 中間生成ファイルのパスも定義しておくと便利
        self.results = {
            "analysis": self.output_dir / "analysis_result.json",
            "geography": self.output_dir / "geography_result.json",
            "agenda": self.output_dir / "agenda_result.json",
            "protagonist": self.output_dir / "protagonist_result.json",
            "deuteragonist": self.output_dir / "deuteragonist_result.json",
            "plot": self.output_dir / "plot_result.json",
        }

        # 必要に応じてディレクトリを作成（存在しなくてもエラーにしない）
        self._ensure_directories()

    def _ensure_directories(self):
        """必要なディレクトリが存在することを確認し、なければ作成する"""
        for directory in [
                self.output_dir, 
                self.scene_dir, 
                self.scenario_dir, 
                self.script_dir, 
                self.drama_dir
            ]:

            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_from_json(cls, config_path: Path) -> "Project":
        config_path = Path(config_path).resolve()
        
        if not config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 配列の最初の要素から "Project" データを取得
        data = config_data["Project"]
        
        # 引数に base_path を追加してインスタンス化
        return cls(
            project_name=data.get("project_name", ""),
            description=data.get("description", ""),
            project_dir=Path(data.get("project_dir", ".")),
            gis_data=Path(data.get("gis_data", "")),
            rubi_map=Path(data.get("rubi_map", "")),
            base_path=config_path.parent,
            llm_client=data.get("llm_client", ""),
            llm_model=data.get("llm_model", ""),
            llm_api=data.get("llm_api", ""),
            tts_client=data.get("tts_client", ""),
            tts_model=data.get("tts_model", ""),
            tts_api=data.get("tts_api", "")
        )

    def __str__(self):
        return f"<Project: {self.project_name} at {self.project_dir}>"