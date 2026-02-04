#!/bin/bash
set -e

# --- 設定項目 ---
# /opt/rocm がシンボリックリンクでない場合は rocm-6.2 等の実体を指定してください
ROCM_PATH="/opt/rocm"
GPU_TARGET="gfx1100"
TEMP_DIR="flash-attention-build"

echo "🚀 ROCm 用 Flash Attention のビルドを開始します（Torch 保護モード）"

# 1. 現状の Torch 確認 (ROCm版でないなら中止)
echo "🔍 Torch のバージョンを確認中..."
python3 -c "import torch; print(f'Using Torch: {torch.__version__}'); assert 'rocm' in torch.__version__" || (echo "❌ エラー: ROCm版 Torch が venv に見つかりません。"; exit 1)

# 2. 環境変数のセットアップ
export PATH="${ROCM_PATH}/bin:${ROCM_PATH}/llvm/bin:${PATH}"
export LD_LIBRARY_PATH="${ROCM_PATH}/lib:${LD_LIBRARY_PATH}"
export ROCM_HOME="${ROCM_PATH}"

# 【重要】ビルドシステムに AMD 向けであることを強制認識させるフラグ
export FLASH_ATTENTION_FORCE_ROCM=1
export FLASH_ATTENTION_FORCE_BUILD=1
export GPU_ARCHS="${GPU_TARGET}"
export PYTORCH_ROCM_ARCH="${GPU_TARGET}"

# 3. ソース取得
if [ -d "$TEMP_DIR" ]; then rm -rf "$TEMP_DIR"; fi
echo "📥 ROCm 公式ソースコードをクローン中..."
git clone --recursive https://github.com/ROCm/flash-attention.git "$TEMP_DIR"
cd "$TEMP_DIR"

# 4. ビルドとインストール
echo "🏗️  ビルドを開始します。hipcc が動くため 10分〜20分かかります..."

# --- 3.5 setup.py の allowed_archs に gfx1100 を追加 ---
echo "🔧 setup.py に gfx1100 を登録中..."
sed -i 's/"gfx942"\]/"gfx942", "gfx1100"\]/g' setup.py

# 念のため置換が成功したか確認表示
grep "allowed_archs =" setup.py

# --no-deps: Torch 等を勝手にダウンロードさせない
# --no-build-isolation: 現在の venv 環境でビルドする
# --verbose: コンパイル（hipcc）のログをリアルタイム表示する
MAX_JOBS=$(nproc) pip install . \
    --no-deps \
    --no-build-isolation \
    --no-cache-dir \
    --verbose

echo "✅ インストール完了！テストを実行します..."
cd ..
python3 -c "import flash_attn; print('✨ 大成功! Version:', flash_attn.__version__)"