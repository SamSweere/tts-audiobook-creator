import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from tts_audiobook_creator.utils import get_project_root_path, load_config

logger = logging.getLogger(__name__)


class BaseTTS(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    def speak(self, text: str, output_file_path: Path) -> Path:
        """
        Convert text to speech and save it to a file.

        Args:
            text (str): The text to convert to speech.
            output_file_path (Path): The full path where the output audio file will be saved.

        Returns:
            Path: The path to the generated audio file.
        """
        pass

    # Add any shared functions here


def get_tts(tts_engine: str | None = None) -> BaseTTS:
    """
    Create a TTS engine.

    Args:
        tts_engine (str | None, optional): TTS engine to create.
            When None, it reads from the config file. Defaults to None.

    Raises:
        ValueError: When an unknown TTS engine is provided.

    Returns:
        BaseTTS: The TTS engine.
    """
    # Load the TTS configuration
    tts_config: dict[str, Any] = load_config()["tts"]

    if not tts_engine:
        tts_engine = tts_config["engine"]
        logger.info(f"Using TTS engine loaded from config: {tts_engine}")
    else:
        logger.info(f"Using TTS engine passed to function: {tts_engine}")

    tts_engine = tts_engine.lower()

    # if tts_engine == "pyttsx3":
    #     from tts_audiobook_creator.tts.pyttsx3 import Pyttsx3TTS
    #     return Pyttsx3TTS()

    if tts_engine == "xtts":
        from tts_audiobook_creator.tts.xtts import XTTS

        return XTTS(
            speaker_path=tts_config["XTTS"]["speaker_path"],
            language=tts_config["language"],
        )
    elif tts_engine == "openai":
        from tts_audiobook_creator.tts.openai_tts import OpenAITTS

        return OpenAITTS(
            model=tts_config["openai"]["model"],
            voice=tts_config["openai"]["voice"],
        )
    else:
        raise ValueError(f"Unknown TTS engine: {tts_engine}")


if __name__ == "__main__":
    # Example usage
    tts = get_tts("openai")  # or get_tts("openai"), or get_tts() to use config
    output_file_path = get_project_root_path() / "data" / "output" / "tts_test" / "test.mp3"
    result = tts.speak("Hello there, General Kenobi!", output_file_path)
    print(f"Audio saved to: {result}")
