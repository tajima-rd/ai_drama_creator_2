#!/bin/bash
set -e

# --- 設定 ---
REPO_URL="https://github.com/QwenLM/Qwen3-TTS.git"

# スクリプト自身の場所を基準に、常にプロジェクトルート直下の
# third_party/ 配下に展開されるようにする。
# third_party/ に置く理由:
#   - 自前のコードと、外部からクローンしてくる依存を、ディレクトリの
#     時点で明確に区別するため。
#   - このプロジェクト自体がgit管理されているため、qwen3-tts が持つ
#     独自の .git（git clone してくると付いてくる）が、プロジェクト
#     本体のgit管理と衝突（いわゆる "nested repo" 問題）しないよう、
#     third_party/ ごと .gitignore で除外する運用にするため
#     （このスクリプトはクリーンインストールのたびに再クローンする
#     設計なので、コミット対象として管理する必要はない）。
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
THIRD_PARTY_DIR="${PROJECT_ROOT}/third_party"
TEMP_DIR="${THIRD_PARTY_DIR}/qwen3-tts"

mkdir -p "$THIRD_PARTY_DIR"

echo "🚀 Qwen3-TTS のインストールを開始します..."
echo "   展開先: ${TEMP_DIR}"

# 1. システム依存関係の確認 (Ubuntu/Debian想定)
# 音声処理に必須のライブラリを確認
echo "📦 システムライブラリ(sox, ffmpeg)を確認中..."
sudo apt-get update && sudo apt-get install -y sox libsox-dev ffmpeg || echo "⚠️ sudo権限がないためスキップします。必要に応じて手動でインストールしてください。"

# 2. ソース取得
if [ -d "$TEMP_DIR" ]; then
    echo "🧹 既存のディレクトリを削除してクリーンインストールします..."
    rm -rf "$TEMP_DIR"
fi

echo "📥 Qwen3-TTS をクローン中..."
git clone "$REPO_URL" "$TEMP_DIR"
cd "$TEMP_DIR"

# 3. 依存関係のインストール
# Flash Attention が既に ROCm 版で入っていることを前提に、
# 他の依存関係を上書きされないようにインストールします。
echo "🏗️  Python 依存パッケージをインストール中..."
pip install --upgrade pip
# matcha-tts などのビルドに失敗しないよう、先に基本ツールを最新にする
pip install setuptools wheel Cython

# 本体と依存関係のインストール
# ※ Flash Attention が既に適切に入っていれば、ここで再ビルドは走りません
pip install -e .

# 4. 仕上げ：パスの通った環境で動作確認
echo "🔍 インストール状況を確認中..."
python3 -c "import qwen_tts; print('✨ インポート成功！ Version:', qwen_tts.__version__ if hasattr(qwen_tts, '__version__') else 'unknown')"

echo "✅ すべての工程が完了しました！"