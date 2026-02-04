import requests
import json
import uvicorn
import time
import multiprocessing

from pydantic import BaseModel
from enum import Enum
from typing import List, Dict, Optional, Any
from .server import app as server_app
from ...models.drama import Character

class MCPClientManager:
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.server_url = f"http://{self.host}:{self.port}"
        self._server_process: Optional[multiprocessing.Process] = None

    def _run_server_process(self):
        uvicorn.run(server_app, host=self.host, port=self.port)

    def start_server(self, wait: bool = True) -> bool:
        if self._server_process and self._server_process.is_alive():
            print("サーバーは既に起動しています。")
            return True

        print("MCPサーバーをバックグラウンドで起動します...")
        self._server_process = multiprocessing.Process(target=self._run_server_process)
        self._server_process.start()
        
        if wait:
            return self.wait_for_server_ready()
        return True

    def wait_for_server_ready(self, retries: int = 10, delay: int = 1) -> bool:
        print("サーバーの起動を待っています...")
        health_endpoint = f"{self.server_url}/health"
        for i in range(retries):
            try:
                response = requests.get(health_endpoint, timeout=1)
                if response.status_code == 200:
                    print("サーバーが起動しました。")
                    return True
            except requests.ConnectionError:
                time.sleep(delay)
        
        print("サーバーの起動に失敗しました。")
        return False

    def shutdown_server(self):
        if self._server_process and self._server_process.is_alive():
            print("\nMCPサーバーをシャットダウンします。")
            self._server_process.terminate()
            self._server_process.join()
            self._server_process = None
            print("サーバーをシャットダウンしました。")
        else:
            print("サーバーは起動していません。")

    def configure(self, configs: List[Any]) -> bool:
        # 1. 引数の型をチェックし、辞書のリスト (configs_data) に変換
        configs_data = []
        if not configs:
            print("設定データが空です。")
            return False

        try:
            for config in configs:
                # Pydantic モデル (GeneratorConfig など) かどうかチェック
                if isinstance(config, BaseModel):
                    if hasattr(config, 'model_dump'):
                        configs_data.append(config.model_dump()) # v2
                    else:
                        configs_data.append(config.dict()) # v1
                
                # 辞書型かどうかチェック
                elif isinstance(config, dict):
                    configs_data.append(config)
                
                # それ以外はエラー
                else:
                    print(f"サポート外の config 型です: {type(config)}")
                    return False
        except Exception as e:
            print(f"設定データの辞書変換中にエラーが発生しました: {e}")
            return False

        configure_endpoint = f"{self.server_url}/configure"
        request_body = {"configs": configs_data}
        
        # 送信する内容を整形して表示 (デバッグ用)
        print(f">>> MCPサーバー ({configure_endpoint}) に設定を送信します...")
        try:
            print(f"/configure へ設定をPOSTします: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        except TypeError:
            print(f"/configure へ設定をPOSTします (JSONシリアライズ不可なデータあり)")

        try:
            response = requests.post(
                configure_endpoint,
                json=request_body, 
                timeout=10
            )
            response.raise_for_status() # 4xx, 5xx エラーで例外を発生させる
            
            response_data = response.json()
            print(f"サーバーの設定が完了しました。")
            print(f"MCPサーバー設定成功。利用可能なモデル: {response_data.get('configured_generators')}")
            return True

        except requests.exceptions.ConnectionError:
            print(f"/configure 呼び出し失敗: サーバー ({self.server_url}) に接続できません。")
            return False
        except requests.exceptions.RequestException as e: # HTTPError や TimeoutError をキャッチ
            print(f"/configure 呼び出し中にHTTPエラー: {e}")
            # サーバーからのエラーレスポンスが取得できれば表示
            if hasattr(e, 'response') and e.response is not None:
                print(f"サーバーからのエラーメッセージ (Status {e.response.status_code}): {e.response.text}")
            return False
        except Exception as e:
            # その他の予期せぬエラー (JSON デコード失敗など)
            print(f"/configure 呼び出し中に予期せぬエラー: {e}")
            return False

    def generate_text(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        generate_endpoint = f"{self.server_url}/generate_text" # エンドポイント名を確認
        request_data = {"model": model, "messages": messages}
        
        print(f">>> MCPサーバーに '{model}' モデルでリクエストを送信します...")
        
        # ★★★ この try...except ブロックを復元する ★★★
        try:
            response = requests.post(
                generate_endpoint,
                data=json.dumps(request_data),
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("response_text")

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTPエラーが発生しました: {http_err}")
            # 'response'変数がこのスコープに存在することを保証するため、エラーハンドリングを修正
            if 'response' in locals() and response:
                print(f"サーバーからのエラーメッセージ: {response.text}")
        except requests.exceptions.RequestException as req_err:
            print(f"サーバーへの接続中にエラーが発生しました: {req_err}")
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")
        
        return None

    def generate_speech(self, model: str, ssml_text: str, characters: List[Any], output_filename: str) -> Optional[str]:
        speech_endpoint = f"{self.server_url}/generate_speech"
        
        # Characterオブジェクトのリストを、JSONで送信可能な辞書のリストに変換
        char_list_dict = []
        for char in characters:
            char_dict = char.__dict__.copy() # オブジェクトを辞書に
            # voice属性がEnumインスタンスの場合、その名前(文字列)に変換
            if 'voice' in char_dict and isinstance(char_dict['voice'], Enum):
                char_dict['voice'] = char_dict['voice'].name
            char_list_dict.append(char_dict)

        request_data = {
            "model": model,
            "ssml_text": ssml_text,
            "characters": char_list_dict,
            "output_filename": output_filename
        }
        
        print(f">>> MCPサーバーに '{model}' モデルで音声生成リクエストを送信します...")
        
        try:
            response = requests.post(
                speech_endpoint,
                data=json.dumps(request_data, default=str),
                headers={"Content-Type": "application/json"},
                timeout=180 # 音声生成は時間がかかる場合がある
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("file_path")
        except Exception as e:
            print(f"音声生成リクエスト中にエラーが発生しました: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"サーバーからのエラーメッセージ: {response.text}")
            return None