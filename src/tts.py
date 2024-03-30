from pathlib import Path

import torch
from TTS.api import TTS


class AUDIOBOOK_TTS:
    def __init__(self) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Init TTS
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)

    def speak(self, text: str, output_path: Path, speaker_path: Path, language: str) -> None:
        # Text to speech to a file
        self.tts.tts_to_file(
            text=text,
            speaker_wav=str(speaker_path),
            language=language,
            file_path=str(output_path),
        )