#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required." >&2
  exit 1
fi

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y python3-pip python3-venv python3-dev ffmpeg portaudio19-dev libasound2-dev build-essential cmake curl
fi

mkdir -p models voice

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install vosk

cat > .env.example <<'EOF'
STT_MODEL=vosk-model-small-en-us-0.15
LLM_MODEL=qwen2.5-0.5b-instruct-q4_k_m.gguf
TTS_VOICE=en_US-lessac-medium
MIC_CARD=0
EOF

echo ""
echo "Offline assistant scaffold ready."
echo "Next steps on Raspberry Pi:"
echo "  1. Download a Vosk model into models/ and ensure it matches STT_MODEL"
echo "  2. Build or download llama.cpp and place the GGUF model in models/"
echo "  3. Download a Piper voice model into voice/"
echo "  4. Run ./run.sh"
