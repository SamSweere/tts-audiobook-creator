import asyncio
import logging
import os
from pathlib import Path

import openai
from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio

from tts_audiobook_creator.tts import BaseTTS
from tts_audiobook_creator.tts.utils import split_text, stitch_audio
from tts_audiobook_creator.utils import get_project_root_path

logger = logging.getLogger(__name__)


class OpenAITTS(BaseTTS):
    """
    A text-to-speech class using OpenAI's API with a synchronous interface.

    This class provides methods to convert text to speech using OpenAI's TTS models.
    It processes multiple chunks of text concurrently and stitches the
    resulting audio files together, while exposing a synchronous interface.

    Attributes:
        model (str): The OpenAI TTS model to use.
        voice (str): The voice to use for speech synthesis.
        tmp_audio_path (Path): The directory for temporary audio files.
        client (openai.AsyncOpenAI): The asynchronous OpenAI client.
    """

    def __init__(self, model: str = "tts-1", voice: str = "alloy") -> None:
        """
        Initializes the OpenAITTS instance.

        Args:
            model (str, optional): The OpenAI TTS model to use. Defaults to "tts-1".
            voice (str, optional): The voice to use for speech synthesis. Defaults to "alloy".
        """
        logger.debug("Initializing OpenAITTS instance...")
        self.model = model
        self.voice = voice
        self.tmp_audio_path = get_project_root_path() / "data" / "tmp"
        self.tmp_audio_path.mkdir(parents=True, exist_ok=True)

        # Load environment variables
        load_dotenv()

        # Set up OpenAI API client
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.debug("OpenAITTS instance initialized successfully.")

    async def _text_to_speech(self, text: str, filename: str) -> Path:
        """
        Converts a single chunk of text to speech using the OpenAI API.

        Args:
            text (str): The text to convert to speech.
            filename (str): The name of the file to save the audio to.

        Returns:
            Path: The path to the saved audio file.
        """
        logger.info(f"Converting text to speech for file: {filename}")
        tmp_audio_path = self.tmp_audio_path / filename
        async with self.client.audio.speech.with_streaming_response.create(
            input=text, model=self.model, voice=self.voice
        ) as response:
            with open(tmp_audio_path, "wb") as f:
                async for chunk in response.iter_bytes():
                    f.write(chunk)

        logger.info(f"Text to speech conversion complete for file: {filename}")
        return tmp_audio_path

    async def _process_chunks(self, chunks: list[str]) -> list[Path]:
        """
        Processes multiple chunks of text concurrently, converting each to speech.

        Args:
            chunks (list[str]): A list of text chunks to convert to speech.

        Returns:
            list[Path]: A list of paths to the generated audio files.
        """
        logger.info("Processing text chunks concurrently...")
        tasks = [self._text_to_speech(chunk, f"tmp_audio_{i}.mp3") for i, chunk in enumerate(chunks)]
        audio_files = await tqdm_asyncio.gather(*tasks, desc="Text to Speech")
        logger.info("Text chunks processed successfully.")
        return audio_files

    async def _async_speak(self, text: str, output_file_path: Path) -> Path:
        """
        Asynchronously converts the given text to speech, saves it as an audio file, and returns the file path.

        Args:
            text (str): The text to convert to speech.
            output_file_path (Path): The full path where the output audio file will be saved.

        Returns:
            Path: The path to the final audio file.
        """
        logger.info("Starting asynchronous text-to-speech conversion...")
        chunks = split_text(text)

        logger.info("Converting text chunks to speech...")
        audio_files = await self._process_chunks(chunks)

        await asyncio.to_thread(stitch_audio, audio_files, output_file_path)

        logger.info("Cleaning up temporary files...")
        await asyncio.gather(*[asyncio.to_thread(os.remove, file) for file in audio_files])
        logger.info("Cleanup complete")

        return output_file_path

    def speak(self, text: str, output_file_path: Path) -> Path:
        """
        Converts the given text to speech, saves it as an audio file, and returns the file path.

        This method provides a synchronous interface to the asynchronous text-to-speech process.
        It handles the creation and management of the event loop internally.

        Args:
            text (str): The text to convert to speech.
            output_file_path (Path): The full path where the output audio file will be saved.

        Returns:
            Path: The path to the final audio file.
        """
        logger.info(f"Starting synchronous text-to-speech conversion for file: {output_file_path}")
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        result = asyncio.run(self._async_speak(text, output_file_path))
        logger.info(f"Synchronous text-to-speech conversion complete for file: {output_file_path}")
        return result


if __name__ == "__main__":
    """
    Main function to demonstrate the usage of OpenAITTS.
    """
    output_file_path = get_project_root_path() / "data" / "output" / "openai_tts" / "test.mp3"
    tts = OpenAITTS()
    output_file = tts.speak("Hello there, General Kenobi!", output_file_path)
    logger.info(f"Audio file generated at: {output_file}")
