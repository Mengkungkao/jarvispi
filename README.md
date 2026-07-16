# JavisPi 🤖

An offline voice assistant that runs entirely on a Raspberry Pi.
No cloud, no API keys, no internet needed after setup.
Listens → thinks → talks back.

## Hardware

- Raspberry Pi 3B (dev machine) / Pi Zero 2W (final target)
- USB microphone — **the Pi's 3.5mm jack is output-only, it cannot take a mic!**
- Speaker via HDMI monitor for now, PiSugar Whisplay HAT coming soon

## The Stack

| Job | Tool | Size |
|-----|------|------|
| Ears (STT) | Vosk small EN model | ~40MB |
| Brain (LLM) | llama.cpp + Qwen2.5-0.5B Q4 | ~400MB |
| Voice (TTS) | Piper (lessac medium voice) | ~60MB |

## Install

On a fresh Raspberry Pi OS (32-bit) with internet:

```bash
git clone https://github.com/YOURUSERNAME/javispi.git
cd javispi
bash install.sh
```

Takes about an hour — compiling llama.cpp is the slow part. The script is
safe to re-run: it skips anything already downloaded or built.

## Before first run

1. Set audio output to HDMI: `sudo raspi-config` → System Options → Audio → HDMI
2. Plug in the USB mic, confirm it shows up: `arecord -l`
3. Quick mic test: `arecord -D plughw:1,0 -f cd -d 5 test.wav && aplay test.wav`

## Run

```bash
./run.sh
```

Press ENTER, speak, wait, listen. Ctrl+C to quit.

The first reply is slow because the model has to load — later replies are faster.

## How it works

```
[ENTER key] → Vosk listens via mic → text
           → llama.cpp thinks      → reply text
           → Piper speaks          → audio out (HDMI)
```

`main.py` keeps the display and talk-trigger behind a small abstraction
(`ConsoleDisplay`), so swapping in the Whisplay HAT's LCD, button, and RGB
LED later only means adding a new display class — the core loop stays the same.

## Roadmap

- [x] Monitor + USB mic version (Pi 3B)
- [ ] Whisplay HAT version: LCD status screens, push-to-talk button, RGB LED
- [ ] Move to Pi Zero 2W + PiSugar battery = pocket Javis

## Notes to self

- Mic card number: check with `arecord -l` (main.py auto-picks the first input device)
- If replies are too slow, lower `MAX_REPLY_TOKENS` in main.py
- llama.cpp lives at `~/llama.cpp`, models live in `./models/`
