# JavisPi 🤖

An offline voice assistant that runs entirely on a Raspberry Pi.
No cloud, no API keys, no internet needed after setup.
Listens → thinks → talks back.

## Hardware

- Raspberry Pi 3B (dev machine) / Pi Zero 2W (final target)
- Mic + speaker: a Bluetooth headset, or a USB microphone + HDMI speaker
  — **the Pi's 3.5mm jack is output-only, it cannot take a mic!**
- PiSugar Whisplay HAT coming soon

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

### Option A: Bluetooth headset (mic + speaker in one)

Pair it once (put the headset in pairing mode first):

```bash
bluetoothctl
  power on
  agent on
  scan on          # wait until your headset's MAC address appears
  pair XX:XX:XX:XX:XX:XX
  trust XX:XX:XX:XX:XX:XX    # auto-reconnect from now on
  connect XX:XX:XX:XX:XX:XX
  exit
```

Check it with `wpctl status` — the headset should be listed under both
Sinks (speaker) and Sources (mic). If no Source shows up, force the
headset profile: find the card id in `wpctl status`, then
`wpctl set-profile <id> headset-head-unit`.

Quick test: `arecord -f S16_LE -r 16000 -d 5 test.wav && aplay test.wav`

Note: while the mic is active the headset runs in headset (HFP) mode, so
playback is phone-call quality — that's a Bluetooth limitation, fine for
a voice assistant.

Troubleshooting:

- `Failed to set power on: org.bluez.Error.Failed` — check `rfkill list`
  and `sudo rfkill unblock bluetooth` if soft-blocked; if
  `dmesg | grep -i brcm` shows a firmware load failure, install the Pi
  bluetooth packages: `sudo apt install -y bluez-firmware pi-bluetooth`
  and reboot.
- `Failed to connect: ... br-connection-profile-unavailable` — PipeWire's
  Bluetooth plugin isn't loaded yet (it only registers audio profiles
  with BlueZ when WirePlumber starts). Reboot, or run
  `systemctl --user restart pipewire pipewire-pulse wireplumber`, then
  connect again.

### Option B: USB mic + HDMI speaker

1. Set audio output to HDMI: `sudo raspi-config` → System Options → Audio → HDMI
2. Plug in the USB mic, confirm it shows up: `arecord -l`
3. Quick mic test: `arecord -D plughw:1,0 -f cd -d 5 test.wav && aplay test.wav`

## Run

```bash
./run.sh
```

Press ENTER, speak, press ENTER again when done, wait, listen. Ctrl+C to quit.

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
