#!/usr/bin/env python3
"""
JavisPi - Offline voice assistant for Raspberry Pi
Listens (Vosk) -> Thinks (llama.cpp) -> Speaks (Piper)

Monitor edition: terminal = display, ENTER key = push-to-talk.
Later, swap ConsoleDisplay for WhisplayDisplay without touching the loop.
"""

import os
import sys
import json
import time
import queue
import subprocess

try:
    import sounddevice as sd
    from vosk import Model, KaldiRecognizer
except ImportError:
    print("Missing packages. Activate the venv first:")
    print("  source venv/bin/activate")
    sys.exit(1)

# ---------------------------------------------------------------
# Paths (portable - everything relative to this file)
# ---------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
VOSK_MODEL = os.path.join(BASE, "models", "vosk-model-small-en-us-0.15")
LLM_MODEL = os.path.join(BASE, "models", "qwen2.5-0.5b-instruct-q4_k_m.gguf")
PIPER_BIN = os.path.join(BASE, "piper", "piper")
PIPER_VOICE = os.path.join(BASE, "models", "en_US-lessac-medium.onnx")
LLAMA_BIN = os.path.expanduser("~/llama.cpp/build/bin/llama-cli")

SAMPLE_RATE = 16000
MAX_REPLY_TOKENS = "60"

SYSTEM_PROMPT = (
    "You are Javis, a friendly voice assistant running on a Raspberry Pi. "
    "Answer briefly in one or two short sentences."
)


# ---------------------------------------------------------------
# Display abstraction (swap for Whisplay LCD later)
# ---------------------------------------------------------------
class ConsoleDisplay:
    def status(self, text):
        print(f"\n[STATUS] {text}")

    def thinking(self, elapsed, frame):
        print(f"\r[STATUS] Thinking {frame}  {elapsed}s ", end="", flush=True)

    def clear_line(self):
        print("\r" + " " * 70 + "\r", end="", flush=True)

    def show_user(self, text):
        print(f"YOU:  {text}")

    def show_bot(self, text):
        print(f"BOT:  {text}")

    def error(self, text):
        print(f"[ERROR] {text}")


display = ConsoleDisplay()


# ---------------------------------------------------------------
# Startup checks
# ---------------------------------------------------------------
def check_files():
    problems = []
    if not os.path.isdir(VOSK_MODEL):
        problems.append(f"Vosk model missing: {VOSK_MODEL}")
    if not os.path.isfile(LLM_MODEL):
        problems.append(f"LLM model missing: {LLM_MODEL}")
    if not os.path.isfile(LLAMA_BIN):
        problems.append(f"llama-cli missing: {LLAMA_BIN}")
    if not os.path.isfile(PIPER_BIN):
        problems.append(f"Piper missing: {PIPER_BIN}")
    if not os.path.isfile(PIPER_VOICE):
        problems.append(f"Piper voice missing: {PIPER_VOICE}")
    if problems:
        display.error("Setup incomplete. Run: bash install.sh")
        for p in problems:
            print("  -", p)
        sys.exit(1)


def pick_mic():
    """Prefer the system default route (PipeWire/Pulse) so Bluetooth mics
    work; fall back to the first raw device with input channels (USB mic)."""
    try:
        devices = sd.query_devices()
        for wanted in ("pipewire", "pulse", "default"):
            for idx, dev in enumerate(devices):
                if dev["max_input_channels"] > 0 and wanted in dev["name"].lower():
                    display.status(f"Using mic: {dev['name']} (device {idx})")
                    return idx
        for idx, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                display.status(f"Using mic: {dev['name']} (device {idx})")
                return idx
    except Exception as e:
        display.error(f"Could not query audio devices: {e}")
    display.error("No microphone found. Plug in a USB mic or connect a Bluetooth headset.")
    sys.exit(1)


# ---------------------------------------------------------------
# The three stages
# ---------------------------------------------------------------
def listen(model, mic_index):
    """Record from mic until Vosk detects end of utterance, return text."""
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    audio_q = queue.Queue()

    def callback(indata, frames, time_info, status):
        audio_q.put(bytes(indata))

    display.status("Listening... speak now")
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        device=mic_index,
        callback=callback,
    ):
        while True:
            data = audio_q.get()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "").strip()
                if text:
                    print()  # end the partial-results line
                    return text
            else:
                # live feedback so you can see the mic is actually working
                partial = json.loads(rec.PartialResult()).get("partial", "")
                if partial:
                    print(f"\r  (hearing: {partial[-60:]})", end="", flush=True)


def think(prompt):
    display.status("Thinking... (first run is slow while the model loads)")
    # llama-cli is a chat client now: stdout carries spinner/banner noise, so
    # we ask for a single turn (-st) and read the clean reply from a file (-o).
    reply_file = "/tmp/javispi_reply.txt"
    if os.path.exists(reply_file):
        os.remove(reply_file)
    cmd = [
        LLAMA_BIN,
        "-m", LLM_MODEL,
        "-sys", SYSTEM_PROMPT,
        "-p", prompt,
        "-n", MAX_REPLY_TOKENS,
        "--temp", "0.7",
        "-st",
        "-o", reply_file,
    ]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        start = time.time()
        frames = "|/-\\"
        i = 0
        while proc.poll() is None:
            display.thinking(int(time.time() - start), frames[i % len(frames)])
            i += 1
            time.sleep(0.25)
            if time.time() - start > 180:
                proc.kill()
                proc.wait()
                display.clear_line()
                return "Sorry, that took too long to think about."
        display.clear_line()
        with open(reply_file) as f:
            out = f.read()
        # file format: "User:\n<question>\n\nAssistant:\n<reply>\n"
        reply = out.split("Assistant:", 1)[-1].strip()
        return reply if reply else "Sorry, I came up blank on that one."
    except Exception as e:
        display.error(f"LLM error: {e}")
        return "Something went wrong in my brain."


def speak(text):
    display.status("Speaking...")
    # Feed the text to Piper over stdin - no shell, so the LLM can emit
    # quotes, backticks or $() without breaking (or running!) anything.
    try:
        piper = subprocess.Popen(
            [PIPER_BIN, "--model", PIPER_VOICE, "--output_raw"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        )
        aplay = subprocess.Popen(
            ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
            stdin=piper.stdout,
        )
        piper.stdout.close()  # aplay owns it now; lets it see EOF
        piper.stdin.write(text.encode())
        piper.stdin.close()
        aplay.wait(timeout=120)
        piper.wait(timeout=10)
    except Exception as e:
        display.error(f"TTS error: {e}")


# ---------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------
def main():
    print("=" * 50)
    print("  JavisPi - offline voice assistant")
    print("=" * 50)
    check_files()
    mic_index = pick_mic()

    display.status("Loading speech model...")
    vosk_model = Model(VOSK_MODEL)
    display.status("Ready.")

    while True:
        try:
            input("\nPress ENTER to talk (Ctrl+C to quit)... ")
            heard = listen(vosk_model, mic_index)
            display.show_user(heard)
            reply = think(heard)
            display.show_bot(reply)
            speak(reply)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
