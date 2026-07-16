import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import OfflineAssistant


class OfflineAssistantTests(unittest.TestCase):
    def test_greeting_reply(self) -> None:
        assistant = OfflineAssistant()
        self.assertIn("offline voice assistant", assistant.generate_reply("hello there"))

    def test_quit_reply(self) -> None:
        assistant = OfflineAssistant()
        self.assertEqual("Goodbye.", assistant.generate_reply("quit"))

    def test_env_defaults(self) -> None:
        assistant = OfflineAssistant()
        self.assertEqual("vosk-model-small-en-us-0.15", assistant.stt_model)
        self.assertEqual("qwen2.5-0.5b-instruct-q4_k_m.gguf", assistant.llm_model)


if __name__ == "__main__":
    unittest.main()
