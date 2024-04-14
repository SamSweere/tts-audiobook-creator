import logging
from pathlib import Path

import torch
from TTS.api import TTS

from tts_audiobook_creator.tts.base_tts import BaseTTS

logger = logging.getLogger(__name__)


class XTTS(BaseTTS):
    def __init__(self, output_path: Path | str, speaker_path: Path | str, language: str) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        self.output_path = output_path
        self.speaker_path = speaker_path
        self.language = language

        # Init TTS
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)

        logger.info("Initialized TTS")

    def speak(self, text: str, filename: str) -> Path:
        # Text to speech to a file
        audio_path = self.tts.tts_to_file(
            text=text,
            speaker_wav=str(self.speaker_path),
            language=self.language,
            file_path=str(Path(self.output_path) / filename) + ".wav",
        )

        audio_path = Path(audio_path)

        logger.info(f"Saved audio to {audio_path}")

        return audio_path
