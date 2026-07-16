#!/usr/bin/env python3
"""Offline voice-assistant scaffold for a Raspberry Pi."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent


class OfflineAssistant:
    def __init__(self) -> None:
        self.root = ROOT
        self.models_dir = self.root / "models"
        self.voice_dir = self.root / "voice"
        self.stt_model = os.getenv("STT_MODEL", "vosk-model-small-en-us-0.15")
        self.llm_model = os.getenv("LLM_MODEL", "qwen2.5-0.5b-instruct-q4_k_m.gguf")
        self.tts_voice = os.getenv("TTS_VOICE", "en_US-lessac-medium")
        self.mic_card = os.getenv("MIC_CARD", "0")
        self.runtime_status = self.detect_runtime_tools()

    def _find_binary(self, *names: str) -> Optional[str]:
        for name in names:
            resolved = shutil.which(name)
            if resolved:
                return resolved
        return None

    def detect_runtime_tools(self) -> dict[str, bool]:
        stt_model_path = self.models_dir / self.stt_model
        llm_model_path = self.models_dir / self.llm_model
        tts_candidates = [
            self.voice_dir / f"{self.tts_voice}.onnx",
            self.voice_dir / self.tts_voice / "model.onnx",
        ]
        return {
            "stt_available": bool(self._find_binary("vosk-transcriber", "vosk-cli")) and stt_model_path.exists(),
            "llm_available": bool(self._find_binary("llama-cli")) and llm_model_path.exists(),
            "tts_available": bool(self._find_binary("piper")) and any(path.exists() for path in tts_candidates),
        }

    def transcribe_audio(self, audio_path: Optional[Path] = None) -> str:
        if audio_path is None:
            return ""
        if not self.runtime_status["stt_available"]:
            return f"[transcribed offline placeholder from {audio_path.name}]"

        for binary in ("vosk-transcriber", "vosk-cli"):
            resolved = self._find_binary(binary)
            if resolved and audio_path.exists():
                result = subprocess.run([resolved, str(audio_path)], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
        return f"[transcribed from {audio_path.name}]"

    def _invoke_llm(self, text: str) -> Optional[str]:
        if not self.runtime_status["llm_available"]:
            return None
        binary = self._find_binary("llama-cli")
        if not binary:
            return None
        model_path = self.models_dir / self.llm_model
        if not model_path.exists():
            return None

        result = subprocess.run(
            [binary, "-m", str(model_path), "-p", text, "-n", "64"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[-1].strip()
        return None

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

        if llm_reply := self._invoke_llm(cleaned):
            return llm_reply
        return f"You said: {cleaned}. I’m answering locally in demo mode."

    def _speak_with_piper(self, text: str) -> Optional[Path]:
        if not self.runtime_status["tts_available"]:
            return None
        binary = self._find_binary("piper")
        if not binary:
            return None

        model_path = None
        for candidate in [
            self.voice_dir / f"{self.tts_voice}.onnx",
            self.voice_dir / self.tts_voice / "model.onnx",
        ]:
            if candidate.exists():
                model_path = candidate
                break
        if model_path is None:
            return None

        output_path = Path(tempfile.gettempdir()) / "jarvispi_reply.wav"
        result = subprocess.run(
            [binary, "--model", str(model_path), "--output_file", str(output_path)],
            input=text,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and output_path.exists():
            return output_path
        return None

    def speak_reply(self, text: str) -> str:
        if self._speak_with_piper(text):
            print(f"JarvisPi: {text}")
            return text
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
    parser.add_argument("--audio", type=Path, help="transcribe a WAV file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assistant = OfflineAssistant()

    if args.audio:
        print(assistant.transcribe_audio(args.audio))
        return 0

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
