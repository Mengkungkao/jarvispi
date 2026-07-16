#!/usr/bin/env python3
"""Offline voice-assistant scaffold for a Raspberry Pi."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent


class OfflineAssistant:
    def __init__(self) -> None:
        self.stt_model = os.getenv("STT_MODEL", "vosk-model-small-en-us-0.15")
        self.llm_model = os.getenv("LLM_MODEL", "qwen2.5-0.5b-instruct-q4_k_m.gguf")
        self.tts_voice = os.getenv("TTS_VOICE", "en_US-lessac-medium")
        self.mic_card = os.getenv("MIC_CARD", "0")

    def transcribe_audio(self, audio_path: Optional[Path] = None) -> str:
        if audio_path is None:
            return ""
        return f"[transcribed from {audio_path.name}]"

    def generate_reply(self, text: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return "I’m listening. Say something and I’ll answer offline."

        lowered = cleaned.lower()
        if any(keyword in lowered for keyword in ["hello", "hi", "hey"]):
            return "Hello! I’m JarvisPi, your offline voice assistant."
        if any(keyword in lowered for keyword in ["time", "date"]):
            return "I’m still running in local demo mode, but the pipeline is ready for a Pi deployment."
        if any(keyword in lowered for keyword in ["weather", "temperature"]):
            return "Weather lookup is not wired up yet, but the offline stack is ready to grow."
        if any(keyword in lowered for keyword in ["quit", "exit", "stop"]):
            return "Goodbye."
        return f"You said: {cleaned}. I’m answering locally in demo mode."

    def speak_reply(self, text: str) -> str:
        print(f"JarvisPi: {text}")
        return text

    def run_demo(self) -> None:
        print("JarvisPi demo mode. Type 'quit' to leave.")
        while True:
            try:
                user_text = input("You: ").strip()
            except EOFError:
                print()
                break
            if not user_text:
                continue
            reply = self.generate_reply(user_text)
            self.speak_reply(reply)
            if reply.lower() == "goodbye.":
                break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline voice assistant scaffold")
    parser.add_argument("--demo", action="store_true", help="run in local demo mode")
    parser.add_argument("--text", help="process a single text input")
    parser.add_argument("--loop", action="store_true", help="run the interactive loop")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assistant = OfflineAssistant()

    if args.text:
        reply = assistant.generate_reply(args.text)
        assistant.speak_reply(reply)
        return 0

    if args.demo or args.loop or not sys.stdin.isatty():
        assistant.run_demo()
        return 0

    assistant.run_demo()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
