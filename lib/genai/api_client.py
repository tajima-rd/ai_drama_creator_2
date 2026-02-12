import os
from pathlib import Path
import sys
import json
import requests
from google import genai
from typing import List, Dict, Optional


# ==============================================================================
#  APIキー管理クラス
# ==============================================================================
class ApiKeyManager:
    def __init__(self):
        self.clients = None
        self.current_index = 0
        print("ApiKeyManagerが初期化されました。クライアントを追加してください。")

    def add_client(self, api_client: 'ApiClient'):
        self.clients.append(api_client)
        print(f"クライアント '{type(api_client).__name__}' (モデル: {api_client.model_name}) がマネージャーに追加されました。")

    def get_next_client(self) -> 'ApiClient':
        if not self.clients:
            raise ValueError("クライアントが一つも追加されていません。add_client()メソッドで追加してください。")
        
        client = self.clients[self.current_index]
        print(f"--- クライアント #{self.current_index} ({type(client).__name__}) を使用します ---")
        
        self.current_index = (self.current_index + 1) % len(self.clients)
        
        return client

    def get_clients(self, client_type: str = "all") -> list['ApiClient']:
        if client_type == "all":
            return self.clients
        
        # クラス名から 'ApiClient' を除いた部分で判定 (例: 'GeminiApiClient' -> 'gemini')
        type_str = client_type.lower()
        return [
            client for client in self.clients 
            if type(client).__name__.lower().startswith(type_str)
        ]

    def get_current_client(self) -> 'ApiClient':
        if not self.clients:
            raise ValueError("クライアントが一つも追加されていません。")
        return self.clients[self.current_index]

    def set_client_by_index(self, index: int) -> 'ApiClient':
        if not (0 <= index < len(self.clients)):
            raise IndexError(f"インデックスが範囲外です。0から{len(self.clients) - 1}の間で指定してください。")
        
        self.current_index = index
        print(f"現在のクライアントをインデックス #{index} に設定しました。")
        return self.clients[self.current_index]
    
# ==============================================================================
#  API クライアント (基底クラス)
# ==============================================================================
class ApiClient:
    client_type = "base"

    def __init__(
            self, 
            api_key: Optional[str] = None, 
            model_name: Optional[str] = None

        ):
        self.api_key = api_key
        self.model_name = model_name

# ==============================================================================
#  Gemini API クライアント
# ==============================================================================
class GeminiApiClient(ApiClient):
    client_type = "gemini"
    def __init__(
            self, 
            api_key: str, 
            model_name: str = "gemini-3-flash-preview"
        ):
        super().__init__(api_key, model_name)
        
        self.client = genai.Client(api_key=self.api_key)
        print(f"GeminiApiClientがモデル '{self.model_name}' 用に設定されました。")


# ==============================================================================
#  Qwen3-TTS API クライアント
# ==============================================================================
class Qwen3TTSApiClient(ApiClient):
    client_type = "qwen3tts"

    def __init__(
            self, 
            api_key: str, 
            model_name: str, 
            api_url: str
        ):
        super().__init__(api_key, model_name)    
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        print(f"Qwen3TTS ApiClientがモデル '{self.model_name}' (URL: {self.api_url}) 用に初期化されました。")


class GcpTTSApiClient(ApiClient):
    client_type = "gcp_tts"

    def __init__(
            self, 
            api_key: Optional[str] = None, 
            model_name: Optional[str] = "google-cloud-tts",
            api_config_file: Optional[Path] = None
        ):
        super().__init__(api_key, model_name)   
        self.api_config_file = api_config_file
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.api_config_file
        
        # GCPの認証は環境変数で行うため、ここでは特に処理しない
        print(f"GcpTtsApiClientが設定ファイル '{self.api_config_file}' 用に設定されました。")

# ==============================================================================
#  Llama.cpp API クライアント
# ==============================================================================
class LlamaCppApiClient(ApiClient):
    client_type = "llamacpp"

    def __init__(
            self, 
            api_key: str, 
            model_name: str, 
            api_url: str
        ):
        super().__init__(api_key, model_name)    
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        print(f"LlamaCppApiClientがモデル '{self.model_name}' (URL: {self.api_url}) 用に初期化されました。")
