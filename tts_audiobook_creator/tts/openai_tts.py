import asyncio
import os
from pathlib import Path

import openai
from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio

from tts_audiobook_creator.tts import BaseTTS
from tts_audiobook_creator.tts.utils import split_text, stitch_audio
from tts_audiobook_creator.utils import get_project_root_path


class OpenAITTS(BaseTTS):
    """
    A text-to-speech class using OpenAI's API with a synchronous interface.

    This class provides methods to convert text to speech using OpenAI's TTS models.
    It processes multiple chunks of text concurrently and stitches the
    resulting audio files together, while exposing a synchronous interface.

    Attributes:
        model (str): The OpenAI TTS model to use.
        voice (str): The voice to use for speech synthesis.
        output_path (Path): The directory where final audio files will be saved.
        tmp_audio_path (Path): The directory for temporary audio files.
        client (openai.AsyncOpenAI): The asynchronous OpenAI client.
    """

    def __init__(self, output_path: Path, model: str = "tts-1", voice: str = "alloy") -> None:
        """
        Initializes the OpenAITTS instance.

        Args:
            output_path (Path): The directory where final audio files will be saved.
            model (str, optional): The OpenAI TTS model to use. Defaults to "tts-1".
            voice (str, optional): The voice to use for speech synthesis. Defaults to "alloy".
        """
        self.model = model
        self.voice = voice
        self.output_path = output_path
        self.output_path.mkdir(parents=True, exist_ok=True)  # Create output directory
        self.tmp_audio_path = get_project_root_path() / "data" / "tmp"
        self.tmp_audio_path.mkdir(parents=True, exist_ok=True)

        # Load environment variables
        load_dotenv()

        # Set up OpenAI API client
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def _text_to_speech(self, text: str, filename: str) -> Path:
        """
        Converts a single chunk of text to speech using the OpenAI API.

        Args:
            text (str): The text to convert to speech.
            filename (str): The name of the file to save the audio to.

        Returns:
            Path: The path to the saved audio file.
        """
        tmp_audio_path = self.tmp_audio_path / filename
        response = await self.client.audio.speech.create(model=self.model, voice=self.voice, input=text)
        await response.astream_to_file(tmp_audio_path)
        return tmp_audio_path

    async def _process_chunks(self, chunks: list[str]) -> list[Path]:
        """
        Processes multiple chunks of text concurrently, converting each to speech.

        Args:
            chunks (list[str]): A list of text chunks to convert to speech.

        Returns:
            list[Path]: A list of paths to the generated audio files.
        """
        tasks = [self._text_to_speech(chunk, f"tmp_audio_{i}.mp3") for i, chunk in enumerate(chunks)]
        audio_files = await tqdm_asyncio.gather(*tasks, desc="Text to Speech")
        return audio_files

    async def _async_speak(self, text: str, filename: str) -> Path:
        """
        Asynchronously converts the given text to speech, saves it as an audio file, and returns the file path.

        Args:
            text (str): The text to convert to speech.
            filename (str): The name of the output audio file (without extension).

        Returns:
            Path: The path to the final audio file.
        """
        chunks = split_text(text)

        print("Converting text chunks to speech...")
        audio_files = await self._process_chunks(chunks)

        output_file_path = self.output_path / f"{filename}.mp3"
        await asyncio.to_thread(stitch_audio, audio_files, output_file_path)

        print("Cleaning up temporary files...")
        await asyncio.gather(*[asyncio.to_thread(os.remove, file) for file in audio_files])
        print("Cleanup complete")

        return output_file_path

    def speak(self, text: str, filename: str) -> Path:
        """
        Converts the given text to speech, saves it as an audio file, and returns the file path.

        This method provides a synchronous interface to the asynchronous text-to-speech process.
        It handles the creation and management of the event loop internally.

        Args:
            text (str): The text to convert to speech.
            filename (str): The name of the output audio file (without extension).

        Returns:
            Path: The path to the final audio file.
        """
        return asyncio.run(self._async_speak(text, filename))


if __name__ == "__main__":
    """
    Main function to demonstrate the usage of OpenAITTS.
    """
    output_path = get_project_root_path() / "data" / "output" / "openai_tts"
    tts = OpenAITTS(output_path=output_path)
    output_file = tts.speak("Hello there, general kenobi!", "test")
    print(f"Audio file generated at: {output_file}")
