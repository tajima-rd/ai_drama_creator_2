import os, requests, json
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
from pathlib import Path 

from pydantic import BaseModel, TypeAdapter

# サーバー側で必要なクラスをインポート
from ..genai.api_client import GeminiApiClient, LlamaCppApiClient
from ..genai.generators import GeminiTextGenerator, LlamaCppTextGenerator, GeminiSpeechGenerator
from ..config import WriteConfig, SpeechConfig
from ...models.drama import Character, Voice

class GeneratorConfig(BaseModel):    
    generator_name: str
    client_type: str
    model_name: str
    api_key: str
    api_url: Optional[str] = None

    @classmethod
    def load_from_json(cls, config_path: Path) -> List["GeneratorConfig"]:
        if not config_path.exists():
            print(f"設定ファイルが見つかりません: {config_path}")
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data_list = json.load(f)
            
            # "MCP_Clients" セクションを探す
            clients_data_list = None
            if not isinstance(config_data_list, list):
                 raise ValueError("JSONのルートがリストではありません。")

            for item in config_data_list:
                if isinstance(item, dict) and "GeneratorConfig" in item:
                    clients_data_list = item["GeneratorConfig"]
                    break
            
            if clients_data_list is None:
                raise ValueError("JSON内に 'GeneratorConfig' キーが見つかりません。")

            # Pydantic を使って辞書のリストを GeneratorConfig のリストにパースする
            try:
                # Pydantic v2 (推奨)
                adapter = TypeAdapter(List[cls])
                return adapter.validate_python(clients_data_list)
            except ImportError:
                # Pydantic v1 (フォールバック)
                return None
        
        except json.JSONDecodeError as e:
            print(f"設定ファイルのJSONパースに失敗しました: {config_path} ({e})")
            raise ValueError(f"Failed to parse config file: {e}") from e
        except Exception as e:
            # (Pydantic のバリデーションエラーなどもキャッチ)
            print(f"設定データのパースまたはバリデーションに失敗しました: {e}")
            raise ValueError(f"Failed to parse or validate config data: {e}") from e

class ConfigureRequest(BaseModel):
    configs: List[GeneratorConfig]

class GenerateRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]

class GenerateResponse(BaseModel):
    response_text: str

class SpeechGenerateRequest(BaseModel):
    model: str
    ssml_text: str
    characters: List[Dict]
    output_filename: str

class SpeechGenerateResponse(BaseModel):
    file_path: str
    message: str

app = FastAPI(title="Model Context Protocol (MCP) Server")
GENERATORS: Dict[str, Any] = {}

@app.post("/configure")
def configure_generators(request: ConfigureRequest):
    """
    設定情報を受け取り、サーバー内でジェネレーターをインスタンス化する。
    """
    global GENERATORS
    GENERATORS = {} # 設定のたびにリセット

    print("--- ジェネレーターの設定を開始します ---")
    
    write_config = WriteConfig()
    speech_config = SpeechConfig()

    for config in request.configs:
        try:
            # フラグ: 登録が成功したかどうか
            registered = False

            if config.client_type == "gemini":
                client = GeminiApiClient(api_key=config.api_key, model_name=config.model_name)
                if "text" in config.generator_name:
                    GENERATORS[config.generator_name] = GeminiTextGenerator(api_client=client, write_config=write_config)
                elif "speech" in config.generator_name:
                    GENERATORS[config.generator_name] = GeminiSpeechGenerator(api_client=client, speech_config=speech_config)
                
                registered = True
            
            elif config.client_type == "llamacpp": 
                client = LlamaCppApiClient(api_key=config.api_key, model_name=config.model_name, api_url=config.api_url)
                GENERATORS[config.generator_name] = LlamaCppTextGenerator(api_client=client, write_config=write_config)
                
                registered = True
            
            else:
                # ★ここが重要: 想定外の client_type が来た場合のハンドリング
                print(f"警告: 未知の client_type '{config.client_type}' が指定されました。スキップします。 (Generator: {config.generator_name})")

            # 成功メッセージは、実際に登録された場合のみ出す
            if registered:
                print(f"'{config.generator_name}' のセットアップが完了しました。")

        except Exception as e:
            # 初期化失敗時のエラーハンドリング
            print(f"'{config.generator_name}' のセットアップ中にエラーが発生しました: {e}")
    
    # 最終確認ログ
    print(f"サーバーの設定が完了しました。利用可能なモデル: {list(GENERATORS.keys())}")
    
    return {"message": "Configuration successful.", "configured_generators": list(GENERATORS.keys())}

@app.post("/generate_text", response_model=GenerateResponse)
def generate_text(request: GenerateRequest):
    print(f"\n--- [デバッグ] /generate_text が呼び出されました ---")
    print(f"クライアントからのリクエスト (request.model): {request.model}")
    print(f"現在のサーバー側 GENERATORS リスト: {list(GENERATORS.keys())}")

    generator = GENERATORS[request.model]
    generated_text = generator.generate(request.messages)
    return GenerateResponse(response_text=generated_text)

    # if request.model not in GENERATORS:
    #     raise HTTPException(status_code=404, detail=f"Model '{request.model}' not found.")
    
    # try:
    #     generator = GENERATORS[request.model]
    #     generated_text = generator.generate(request.messages)
    #     return GenerateResponse(response_text=generated_text)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_speech", response_model=SpeechGenerateResponse)
def generate_speech(request: SpeechGenerateRequest):
    if request.model not in GENERATORS:
        raise HTTPException(status_code=404, detail=f"Model '{request.model}' not found.")
    
    try:
        generator = GENERATORS[request.model]
        
        # 受信した辞書リストからCharacterオブジェクトのリストを復元
        # voice属性はEnumのメンバー名(文字列)として渡されることを想定
        characters = []
        for char_data in request.characters:
            # Voice Enumから対応するメンバーを取得
            char_data['voice'] = Voice[char_data['voice']]
            characters.append(Character(**char_data))
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / request.output_filename
        
        result_path = generator.generate(request.ssml_text, characters, output_path)
        
        if result_path is None:
            raise HTTPException(status_code=500, detail="Failed to generate audio file.")
            
        return SpeechGenerateResponse(
            file_path=str(result_path),
            message="Audio file generated successfully."
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "available_models": list(GENERATORS.keys())}
