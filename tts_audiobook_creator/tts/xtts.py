import logging
from pathlib import Path

import torch
from TTS.api import TTS

from tts_audiobook_creator.tts import BaseTTS
from tts_audiobook_creator.utils import get_project_root_path

logger = logging.getLogger(__name__)


class XTTS(BaseTTS):
    """
    A text-to-speech class using the XTTS model.

    This class provides methods to convert text to speech using the XTTS model.
    It supports multiple languages and custom speaker voices.

    Attributes:
        device (str): The device used for TTS processing ('cuda' or 'cpu').
        speaker_path (Path | str): Path to the speaker audio file.
        language (str): The language code for TTS.
        tts (TTS): The TTS model instance.
    """

    def __init__(self, speaker_path: Path | str, language: str) -> None:
        """
        Initialize the XTTS instance.

        Args:
            speaker_path (Path | str): Path to the speaker audio file.
            language (str): The language code for TTS (e.g., 'en' for English).
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        self.speaker_path = speaker_path
        self.language = language

        # Init TTS
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        logger.info("Initialized TTS")

    def speak(self, text: str, output_file_path: Path) -> Path:
        """
        Convert the given text to speech and save it as an audio file.

        This method uses the XTTS model to generate speech from the input text
        and saves it to the specified output file path.

        Args:
            text (str): The text to convert to speech.
            output_file_path (Path): The full path where the output audio file will be saved.

        Returns:
            Path: The path to the generated audio file.
        """
        # Ensure the output directory exists
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Text to speech to a file
        audio_path = self.tts.tts_to_file(
            text=text,
            speaker_wav=str(self.speaker_path),
            language=self.language,
            file_path=str(output_file_path),
        )

        audio_path = Path(audio_path)
        logger.info(f"Saved audio to {audio_path}")
        return audio_path


if __name__ == "__main__":
    # Example usage
    speaker_path = get_project_root_path() / "sample_data" / "voices" / "female_1.wav"
    language = "en"
    tts = XTTS(speaker_path, language)

    output_file_path = get_project_root_path() / "data" / "output" / "xtts_tts" / "test.mp3"
    result = tts.speak("Hello there, General Kenobi!", output_file_path)
    print(f"Audio saved to: {result}")
