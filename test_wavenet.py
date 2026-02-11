import os
from google.cloud import texttospeech

# --- 設定：ダウンロードしたJSONファイルのパスを指定 ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./configure/secret/gcp_tts_credentials.json"

def generate_voice(text, output_file="output.mp3"):
    # クライアントの初期化
    client = texttospeech.TextToSpeechClient()

    # 読み上げテキストの設定
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # 声の設定（WaveNet A: 落ち着いた女性の声 / 無料枠 400万文字）
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        name="ja-JP-Chirp3-HD-Schedar"
    )

    # 音声ファイルの設定（MP3）
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # 音声合成の実行
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # ファイルに保存
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f"成功！音声ファイルを保存しました: {output_file}")

# テスト実行
generate_voice("お疲れ様です。Google Cloudの音声合成テスト、成功です。")