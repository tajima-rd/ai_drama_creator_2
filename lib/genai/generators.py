import abc # 抽象基底クラスを定義するためにインポート
import sys
import json
import requests
from google.genai import types # type: ignore
from pathlib import Path
from typing import (
    List, 
    Dict, 
    Union, 
    Any, 
    Optional,
    Tuple
)
from dataclasses import dataclass
from google.cloud import texttospeech

from .api_client import ApiClient, Qwen3TTSApiClient

@dataclass
class WriteConfig:
    temperature: float = 0.8
    top_p: float = 0.95
    max_output_tokens: int = 8192

@dataclass
class SpeechConfig:
    temperature: float = 1.0

@dataclass
class AudioConfig:
    audioEncoding: str = "MP3"
    speakingRate: float = 1.0   # Speaking rate/speed, in the range [0.25, 2.0]
    pitch: float = 0.0          # Speaking pitch, in the range [-20.0, 20.0]
    volumeGainDb: float = 0.0   # Strongly recommend not to exceed +10 (dB)
    sampleRateHertz: int = 24000
    effectsProfileId: List[str] = ["headphone-class-device"]

class AbstractBaseGenerator(abc.ABC):
    def __init__(
            self, 
            api_client: ApiClient, 
            config: Any
        ):

        if not isinstance(api_client, ApiClient):
            raise TypeError("api_clientはApiClientのサブクラスである必要があります。")
        
        self.api_client = api_client
        self.config = config

    @abc.abstractmethod
    def generate(
            self, 
            prompt: Union[str, List[Dict[str, str]]]
        ) -> Any:
        pass

class TextGenerator(AbstractBaseGenerator):
    def __init__(self, api_client: ApiClient, write_config: WriteConfig):
        super().__init__(api_client, write_config)
        if not isinstance(write_config, WriteConfig):
            raise TypeError("write_configはWriteConfigのサブクラスである必要があります。")

    # このクラス独自のgenerateメソッドを新たに抽象メソッドとして定義
    @abc.abstractmethod
    def generate(self, messages: List[Dict[str, str]]) -> Optional[str]:
        pass

class SoundGenerator(AbstractBaseGenerator):
    def __init__(self, api_client: ApiClient, speech_config: Optional[SpeechConfig] = None):
        super().__init__(api_client, speech_config)

    @abc.abstractmethod
    def generate(
            self, 
            texts: List[Any], 
            languages: Union[str, List[Any]], 
            speakers: List[Any],
            instructs: List[Any],
            output_path: Path
        ) -> Optional[Path]:
        pass

class GeminiTextGenerator(TextGenerator):
    """
    Google Gemini APIを使用したテキスト生成器。
    """
    def _build_gemini_config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_output_tokens=self.config.max_output_tokens
        )

    def generate(self, messages: List[Dict[str, str]]) -> Optional[str]:
        try:
            user_prompt = ""
            for msg in reversed(messages):
                if msg['role'] == 'user':
                    user_prompt = msg['content']
                    break
            if not user_prompt:
                raise ValueError("メッセージリストに 'user' ロールのプロンプトがありません。")

            contents = [types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_prompt)]
            )]
            
            # ヘルパーメソッドを呼び出して設定を構築
            generation_config = self._build_gemini_config()

            stream = self.api_client.client.models.generate_content_stream(
                model=self.api_client.model_name,
                contents=contents,
                config=generation_config,
            )

            full_response = "".join(chunk.text for chunk in stream if chunk.text)
            return full_response.strip()

        except Exception as e:
            print(f"Gemini APIでテキスト生成中にエラーが発生しました: {e}", file=sys.stderr)
            raise

class LlamaCppTextGenerator(TextGenerator):
    def _build_llama_payload(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "model": self.api_client.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
            "stream": False
        }

    def generate(self, messages: List[Dict[str, str]]) -> Optional[str]:
        try:
            # ヘルパーメソッドを呼び出してペイロードを構築
            payload = self._build_llama_payload(messages)
            
            response = requests.post(
                self.api_client.api_url,
                headers=self.api_client.headers,
                data=json.dumps(payload),
                timeout=None
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Llama.cpp APIでエラーが発生しました: {e}", file=sys.stderr)
            raise

class QwenSoundGenerator(SoundGenerator):
    def __init__(self, api_client: Qwen3TTSApiClient):
        # Qwenにはconfigが不要なため、親クラスにはNoneを明示して初期化
        super().__init__(api_client, None)

    def generate(
            self, 
            texts: List[Any], 
            languages: Union[str, List[Any]],
            speakers: List[Any],
            instructs: List[Any],
            output_path: Path
        ) -> Optional[Path]:

        def convert_to_http_params() -> List[Tuple[str, Any]]:
            # サーバー側の引数名 (texts, languages, speakers, instructs) に合わせる
            http_params = [('texts', t) for t in texts]
            http_params += [('languages', l) for l in languages]
            http_params += [('speakers', s) for s in speakers]
            
            if instructs:
                http_params += [('instructs', i) for i in instructs]
            
            return http_params

        # languages が単一文字列の場合はリストに拡張
        if isinstance(languages, str):
            languages = [languages] * len(texts)

        try:
            # api_client から URL を取得してリクエスト
            response = requests.get(
                self.api_client.api_url, 
                params=convert_to_http_params(), 
                headers=self.api_client.headers,
                timeout=None
            )
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
            else:
                print(f"API Error ({response.status_code}): {response.text}", file=sys.stderr)
                return None
                
        except Exception as e:
            print(f"QwenSoundGenerator実行中に例外が発生しました: {e}", file=sys.stderr)
            return None

class GcpSoundGenerator(SoundGenerator):
    def generate(
            text, 
            language: str = "japanese",
            speaker: str = "ja-JP-Chirp3-HD-Schedar",
            audio_config: AudioConfig = None,
            output_path="output.mp3"
        ):

        # クライアントの初期化
        client = texttospeech.TextToSpeechClient()

        # 読み上げテキストの設定
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # 声の設定（WaveNet A: 落ち着いた女性の声 / 無料枠 400万文字）
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            name=speaker
        )

        # 音声ファイルの設定（MP3）
        voice_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=audio_config.speakingRate,
            pitch=audio_config.pitch,
            volume_gain_db=audio_config.volumeGainDb,
            sample_rate_hertz=audio_config.sampleRateHertz,
            effects_profile_id=audio_config.effectsProfileId
        )

        # 音声合成の実行
        response = client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=voice_config
        )

        # ファイルに保存
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
            print(f"成功！音声ファイルを保存しました: {output_path}")



# ==============================================================================
# 音声生成器クラス (抽象)
# ==============================================================================
# class SpeechGenerator(abc.ABC):
#     def __init__(self, api_client: ApiClient, speech_config: SpeechConfig):
#         self.api_client = api_client
#         self.config = speech_config
#         self.audio_processor = AudioProcessor()

#     @abc.abstractmethod
#     def generate(self, ssml_dialog: str, characters: List[Character], output_path: Path) -> Optional[Path]:
#         """
#         SSMLダイアログから音声を生成し、指定されたパスにMP3ファイルとして保存する。

#         Args:
#             ssml_dialog (str): 音声合成するSSML形式のテキスト。
#             Characters (List[Character]): 発話するキャラクターのリスト。
#             output_path (Path): 保存先のMP3ファイルパス。

#         Returns:
#             Optional[Path]: 成功した場合は保存先のファイルパス、失敗した場合はNone。
#         """
#         pass

# class GeminiSpeechGenerator(SpeechGenerator):
#     """
#     Google Gemini APIを使用した音声生成器。
#     """
#     def _build_gemini_speech_config(self, Characters: List[Character]) -> types.GenerateContentConfig:
#         """
#         [内部メソッド] キャラクターリストからGemini用の音声設定を構築する。
#         """
#         num_speakers = len(Characters)
#         speech_config = None

#         if num_speakers == 1:
#             # 単一話者設定
#             voice_config = types.VoiceConfig(
#                 prebuilt_voice_config=types.PrebuiltVoiceConfig(
#                     voice_name=Characters[0].voice.api_name
#                 )
#             )
#             speech_config = types.SpeechConfig(voice_config=voice_config)
#         elif num_speakers > 1:
#             # 複数話者設定
#             speaker_configs = [
#                 types.SpeakerVoiceConfig(
#                     speaker=char.name,
#                     voice_config=types.VoiceConfig(
#                         prebuilt_voice_config=types.PrebuiltVoiceConfig(
#                             voice_name=char.voice.api_name
#                         )
#                     )
#                 ) for char in Characters
#             ]
#             multi_speaker_config = types.MultiSpeakerVoiceConfig(speaker_voice_configs=speaker_configs)
#             speech_config = types.SpeechConfig(multi_speaker_voice_config=multi_speaker_config)

#         if speech_config is None:
#             raise ValueError("音声生成には少なくとも1人のキャラクターが必要です。")

#         return types.GenerateContentConfig(
#             temperature=self.config.temperature,
#             response_modalities=["audio"],
#             speech_config=speech_config
#         )

#     def generate(self, ssml_dialog: str, Characters: List[Character], output_path: Path) -> Optional[Path]:
#         try:
#             # ヘルパーメソッドでGemini用の設定を構築
#             generation_config = self._build_gemini_speech_config(Characters)
            
#             contents = [types.Content(
#                 role="user",
#                 parts=[types.Part.from_text(text=ssml_dialog)]
#             )]

#             stream = self.api_client.client.models.generate_content_stream(
#                 model=self.api_client.model_name,
#                 contents=contents,
#                 config=generation_config,
#             )

#             full_audio_data = bytearray()
#             final_mime_type = None
#             for chunk in stream:
#                 if (chunk.candidates and chunk.candidates[0].content and
#                         chunk.candidates[0].content.parts and chunk.candidates[0].content.parts[0].inline_data):
#                     inline_data = chunk.candidates[0].content.parts[0].inline_data
#                     full_audio_data.extend(inline_data.data)
#                     final_mime_type = inline_data.mime_type
            
#             if not full_audio_data or not final_mime_type:
#                 print("警告: APIから音声データが返されませんでした。")
#                 return None

#             # AudioProcessorを使ってWAV変換とMP3保存を行う
#             wav_bytes = self.audio_processor.convert_to_wav(bytes(full_audio_data), final_mime_type)
#             return self.audio_processor.save_as_mp3(wav_bytes, output_path)

#         except Exception as e:
#             print(f"Gemini APIで音声生成中にエラーが発生しました: {e}", file=sys.stderr)
#             raise

# class LlamaCppSpeechGenerator(SpeechGenerator):
#     """
#     Llama.cppは音声生成をサポートしていません。
#     """
#     def generate(self, ssml_dialog: str, Characters: List[Character], output_path: Path) -> Optional[Path]:
#         print("警告: Llama.cppは音声生成をサポートしていません。", file=sys.stderr)
#         return None