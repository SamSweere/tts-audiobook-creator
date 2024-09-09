from pathlib import Path

from tts_audiobook_creator.tts import BaseTTS


class Pyttsx3TTS(BaseTTS):
    def __init__(self) -> None:
        pass

    def speak(self, text: str, filename: str) -> Path:
        pass
