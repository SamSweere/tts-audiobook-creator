import logging
from abc import ABC, abstractmethod
from pathlib import Path

from tts_audiobook_creator.utils import load_config

logger = logging.getLogger(__name__)


class BaseTTS(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    def speak(self, text: str, filename: str) -> Path:
        pass

    # Add any shared functions here


def get_tts(audiobook_output_dir: Path, tts_engine: str | None = None) -> BaseTTS:
    """Create a TTS engine.

    Args:
        audiobook_output_dir (Path): Location to save the generated audio files.
        tts_engine (str | None, optional): tts engine to create,
            when None it reads it from the config file. Defaults to None.

    Raises:
        ValueError: When an unknown TTS engine is provided.

    Returns:
        BaseTTS: The TTS engine.
    """
    # Load the TTS configuration
    tts_config = load_config()["TTS"]

    if not tts_engine:
        tts_engine = tts_config["engine"]
        logger.info(f"Using TTS engine loaded from config: {tts_engine}")
    else:
        logger.info(f"Using TTS engine passed to function: {tts_engine}")

    tts_engine = tts_engine.lower()

    if tts_engine == "pyttsx3":
        from tts_audiobook_creator.tts.pyttsx3 import Pyttsx3TTS

        return Pyttsx3TTS()
    elif tts_engine == "xtts":
        from tts_audiobook_creator.tts.xtts import XTTS

        return XTTS(
            output_path=audiobook_output_dir,
            speaker_path=str(tts_config["XTTS"]["speaker_path"]),
            language=str(tts_config["language"]),
        )
    elif tts_engine == "openai":
        from tts_audiobook_creator.tts.openai_tts import OpenAITTS

        return OpenAITTS(
            output_path=audiobook_output_dir,
            model=tts_config["openai"]["model"],
            voice=tts_config["openai"]["voice"],
        )
    else:
        raise ValueError(f"Unknown TTS engine: {tts_engine}")
