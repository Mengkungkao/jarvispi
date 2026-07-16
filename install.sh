#!/bin/bash
# JavisPi installer - sets up everything on a fresh Raspberry Pi OS (32-bit)
# Usage: bash install.sh
set -e  # stop on any error

cd "$(dirname "$0")"

echo "==============================================="
echo "  JavisPi installer"
echo "==============================================="

echo ""
echo "=== [1/6] System packages ==="
sudo apt update
sudo apt install -y git python3-pip python3-venv portaudio19-dev \
                    ffmpeg build-essential cmake wget unzip alsa-utils

echo ""
echo "=== [2/6] Python environment ==="
if [ ! -d "venv" ]; then
  python3 -m venv venv --system-site-packages
fi
source venv/bin/activate
pip install vosk sounddevice

echo ""
echo "=== [3/6] Vosk speech model (~40MB) ==="
mkdir -p models && cd models
if [ ! -d "vosk-model-small-en-us-0.15" ]; then
  wget -q --show-progress https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
  unzip -q vosk-model-small-en-us-0.15.zip && rm vosk-model-small-en-us-0.15.zip
else
  echo "Already downloaded, skipping."
fi

echo ""
echo "=== [4/6] LLM model (~400MB) ==="
if [ ! -f "qwen2.5-0.5b-instruct-q4_k_m.gguf" ]; then
  wget -q --show-progress https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
else
  echo "Already downloaded, skipping."
fi

echo ""
echo "=== [5/6] Piper voice engine + voice model ==="
if [ ! -f "en_US-lessac-medium.onnx" ]; then
  wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
  wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
else
  echo "Voice model already downloaded, skipping."
fi
cd ..

ARCH=$(uname -m)
if [ ! -d "piper" ]; then
  echo "Downloading Piper binary for $ARCH..."
  wget -q --show-progress "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_${ARCH}.tar.gz"
  tar -xzf "piper_linux_${ARCH}.tar.gz" && rm "piper_linux_${ARCH}.tar.gz"
else
  echo "Piper already installed, skipping."
fi

echo ""
echo "=== [6/6] Building llama.cpp (slow on Pi - go make coffee) ==="
if [ ! -f "$HOME/llama.cpp/build/bin/llama-cli" ]; then
  if [ ! -d "$HOME/llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp --depth 1 "$HOME/llama.cpp"
  fi
  cd "$HOME/llama.cpp"
  cmake -B build
  cmake --build build --config Release -j4
  cd - > /dev/null
else
  echo "llama.cpp already built, skipping."
fi

echo ""
echo "==============================================="
echo "  ✅ JavisPi installed!"
echo "==============================================="
echo ""
echo "Before first run:"
echo "  1. Set audio output to HDMI:  sudo raspi-config -> System Options -> Audio"
echo "  2. Plug in your USB microphone"
echo "  3. Test the mic:  arecord -l"
echo ""
echo "Then start the bot with:  ./run.sh"
