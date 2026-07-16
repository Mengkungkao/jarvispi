# JavisPi 🤖

An offline voice assistant that runs entirely on a Raspberry Pi.
No cloud, no API keys, no internet needed after setup.
Listens → thinks → talks back.

## Hardware
- Raspberry Pi 3B (development) / Pi Zero 2W (target)
- USB microphone (the Pi 3.5mm jack is output-only)
- Speaker via HDMI monitor, or a PiSugar/Whisplay HAT later

## The stack
- Speech-to-text: Vosk small EN model
- LLM: llama.cpp with Qwen2.5-0.5B Q4
- Text-to-speech: Piper (lessac voice)

## Install
```bash
git clone https://github.com/YOURUSERNAME/javispi.git
cd javispi
bash install.sh
```

The install script prepares a Python virtual environment, creates model folders, and writes an example environment file.

## Run
```bash
./run.sh
```

This starts the local demo mode. Press Enter, type a prompt, and the assistant will respond locally.

## Raspberry Pi notes
- Check your microphone card with `arecord -l` and adjust `MIC_CARD` in the environment file if needed.
- Set audio output to HDMI via `sudo raspi-config` if you are using a monitor speaker.
- The first LLM response is usually slow while the model loads; later replies are faster.

## Project layout
- `main.py`: the offline assistant entry point and demo loop
- `install.sh`: environment and dependency setup helper
- `run.sh`: runs the assistant locally
- `tests/`: regression tests for the assistant logic
