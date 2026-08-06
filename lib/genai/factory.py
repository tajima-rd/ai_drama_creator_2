# lib/genai/factory.py
import os

from . import (
    GeminiApiClient,
    LlamaCppApiClient,
    Qwen3TTSApiClient,
    GcpTTSApiClient,
    QwenSoundGenerator,
    WriteConfig,
    GeminiTextGenerator,
    LlamaCppTextGenerator,
    GcpSoundGenerator,
)
from ..core.project import Project


def build_text_generator(project: Project):
    """
    プロジェクト設定に基づいて、適切なLLMクライアントとテキスト
    ジェネレーターを初期化する。
    """
    # APIキーなどの機密情報は環境変数から取得
    # （LlamaCppなどローカルAPIの場合はダミーでも可）
    gemini_key = os.getenv("GENAI_API_KEY")
    llama_key = os.getenv("LLAMA_API_KEY", "dummy")

    write_config = WriteConfig(temperature=0.7)

    if project.llm_client == "LlamaCpp":
        client = LlamaCppApiClient(
            api_key=llama_key,
            model_name=project.llm_model,
            api_url=project.llm_api
        )
        return LlamaCppTextGenerator(api_client=client, write_config=write_config)

    elif project.llm_client == "Gemini":
        client = GeminiApiClient(
            api_key=gemini_key,
            model_name=project.llm_model
        )
        return GeminiTextGenerator(api_client=client, write_config=write_config)

    else:
        raise ValueError(f"未対応のLLMクライアントです: {project.llm_client}")


def build_voice_generator(project: Project):
    """
    プロジェクト設定に基づいて、適切なTTSクライアントと音声
    ジェネレーターを初期化する。
    """
    tts_key = os.getenv("TTS_API_KEY", "dummy")

    if project.tts_client == "Qwen3TTS":
        client = Qwen3TTSApiClient(
            model_name=project.tts_model,
            api_url=project.tts_api,
            api_key=tts_key
        )
        print(f"Initialized Qwen3TTSApiClient with model: {project.tts_model} and API URL: {project.tts_api}")
        return QwenSoundGenerator(api_client=client)

    elif project.tts_client == "GCPTTS":
        client = GcpTTSApiClient(
            api_key="dummy",
            model_name=project.tts_model,
            api_config_file=project.secret_dir / "gcp_tts_credentials.json"
        )
        print(f"Initialized GcpTTSApiClient with model: {project.tts_model}")
        return GcpSoundGenerator(api_client=client)

    else:
        raise ValueError(f"未対応のTTSクライアントです: {project.tts_client}")