import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from tts_audiobook_creator.arxiv import extract_arxiv_id, process_arxiv_paper
from tts_audiobook_creator.to_tts_text_conversion.ai_to_tts_text_converter import AiToTssTextConverter
from tts_audiobook_creator.tts import BaseTTS, get_tts
from tts_audiobook_creator.utils import load_config

logger = logging.getLogger(__name__)


class ArxivPipelineController:
    """
    Controller class for managing the arXiv paper to audiobook pipeline.

    This class handles the entire process of downloading an arXiv paper,
    converting it to TTS format, and creating an audiobook.
    """

    def __init__(self) -> None:
        """
        Initialize the ArxivPipelineController.

        Raises:
            ValueError: If the required API key is not found in environment variables.
        """
        self.config: dict[str, Any] = load_config()
        logger.debug(f"Loaded config: {self.config}")

        self.output_dir: Path = Path(self.config["output_dir"])
        self.output_dir.mkdir(exist_ok=True)

        self.max_filename_length: int = 50
        self.tts: BaseTTS = get_tts()

        api_key = os.environ.get(self.config["to_tts_text_converter"]["api_key_name"])
        if not api_key:
            raise ValueError(
                f"API Key '{self.config['to_tts_text_converter']['api_key_name']}' not found in environment variables."
            )

        self.text_converter = AiToTssTextConverter(
            model_name=self.config["to_tts_text_converter"]["model_name"], api_key=api_key
        )

    def download_paper(self, arxiv_url: str, save_text: bool = False) -> tuple[str, str, str, str, Path | None]:
        """
        Download and process an arXiv paper.

        Args:
            arxiv_url (str): The URL of the arXiv paper.
            save_text (bool, optional): Whether to save the original text. Defaults to False.

        Returns:
            tuple[str, str, str, str, Path | None]: A tuple containing:
                - arxiv_id (str): The arXiv ID of the paper.
                - title (str): The title of the paper.
                - paper_text (str): The text content of the paper.
                - title_filename (str): A filename-friendly version of the title.
                - saved_path (Path | None): The path where the text was saved, if applicable.
        """
        logger.info(f"Downloading arXiv paper from {arxiv_url}...")
        arxiv_id = extract_arxiv_id(arxiv_url)
        paper_text, title = process_arxiv_paper(arxiv_url)
        title_filename = self._create_title_filename(title)
        logger.info("Paper downloaded and processed successfully.")

        saved_path = None
        if save_text:
            saved_path = self._save_text(paper_text, title_filename, is_tts=False)

        return arxiv_id, title, paper_text, title_filename, saved_path

    def convert_to_tts_format(
        self, paper_text: str, title_filename: str, save_text: bool = False
    ) -> tuple[str, Path | None]:
        """
        Convert paper text to TTS-friendly format.

        Args:
            paper_text (str): The original text of the paper.
            title_filename (str): A filename-friendly version of the title.
            save_text (bool, optional): Whether to save the TTS text. Defaults to False.

        Returns:
            tuple[str, Path | None]: A tuple containing:
                - tts_text (str): The TTS-friendly version of the text.
                - saved_path (Path | None): The path where the TTS text was saved, if applicable.
        """
        logger.info("Converting paper text to TTS-friendly format...")
        tts_text_converter_generator = self.text_converter.convert_text(input_text=paper_text)
        previous_output = ""

        for output in tts_text_converter_generator:
            print(previous_output, end="", flush=True)
            previous_output = output

        tts_text = previous_output

        saved_path = None
        if save_text:
            saved_path = self._save_text(tts_text, title_filename, is_tts=True)

        return tts_text, saved_path

    def convert_to_audiobook(self, tts_text: str, title_filename: str) -> Path:
        """
        Convert TTS text to an audiobook.

        Args:
            tts_text (str): The TTS-friendly text to convert.
            title_filename (str): A filename-friendly version of the title.

        Returns:
            Path: The path where the audiobook was saved.
        """
        output_dir = self.output_dir / title_filename
        output_dir.mkdir(exist_ok=True)
        audio_output_path = output_dir / f"{title_filename}.mp3"

        logger.info(f"Converting the text to an audiobook: {audio_output_path}")
        self.tts.speak(tts_text, audio_output_path)
        logger.info("Audiobook created successfully.")

        return audio_output_path

    def run_pipeline(self, arxiv_url: str, save_text: bool = False) -> tuple[Path, Path | None, Path | None]:
        """
        Run the complete pipeline to download a paper and create an audiobook.

        Args:
            arxiv_url (str): The URL of the arXiv paper.
            save_text (bool, optional): Whether to save intermediate text files. Defaults to False.

        Returns:
            tuple[Path, Path | None, Path | None]: A tuple containing:
                - audio_output_path (Path): The path where the audiobook was saved.
                - original_text_path (Path | None): The path where the original text was saved, if applicable.
                - tts_text_path (Path | None): The path where the TTS text was saved, if applicable.
        """
        arxiv_id, title, paper_text, title_filename, original_text_path = self.download_paper(arxiv_url, save_text)
        tts_text, tts_text_path = self.convert_to_tts_format(paper_text, title_filename, save_text)
        audio_output_path = self.convert_to_audiobook(tts_text, title_filename)

        logger.info(f"arXiv paper {arxiv_id} processed and converted to audiobook successfully.")
        return audio_output_path, original_text_path, tts_text_path

    def _create_title_filename(self, title: str) -> str:
        """
        Create a filename-friendly version of the paper title.

        Args:
            title (str): The original title of the paper.

        Returns:
            str: A filename-friendly version of the title.
        """

        def clean_filename(filename: str) -> str:
            filename = re.sub(r'[<>:"/\\|?*]', "", filename)
            filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)
            filename = re.sub(r"[\s.]+", "_", filename)
            filename = "".join(ch for ch in filename if unicodedata.category(ch)[0] != "C")
            filename = unicodedata.normalize("NFKD", filename).encode("ASCII", "ignore").decode("ASCII")
            filename = filename.strip(". ")
            return filename

        filename = clean_filename(title)
        max_length = max(1, self.max_filename_length)
        parts = filename.split("_")
        result = []
        current_length = 0

        for part in parts:
            if current_length + len(part) + (1 if result else 0) <= max_length:
                if result:
                    current_length += 1
                result.append(part)
                current_length += len(part)
            else:
                break

        if not result:
            result = [filename[:max_length]]

        title_filename = "_".join(result)

        if not title_filename or title_filename.startswith("."):
            title_filename = "untitled" + (title_filename if title_filename else "")

        return title_filename

    def _save_text(self, content: str, title_filename: str, is_tts: bool = False) -> Path:
        """
        Save text content to a file.

        Args:
            content (str): The text content to save.
            title_filename (str): A filename-friendly version of the title.
            is_tts (bool, optional): Whether the content is TTS text. Defaults to False.

        Returns:
            Path: The path where the text was saved.
        """
        output_dir = self.output_dir / title_filename
        output_dir.mkdir(exist_ok=True)

        file_extension = "txt" if is_tts else "tex"
        file_path = output_dir / f"{title_filename}.{file_extension}"

        logger.info(f"Saving the {'TTS' if is_tts else 'original'} text to {file_path}")
        with open(file_path, "w") as text_file:
            text_file.write(content)
        logger.info(f"Paper {'TTS' if is_tts else 'original'} text saved to file successfully.")
        return file_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pipeline = ArxivPipelineController()

    paper_url = "https://arxiv.org/abs/2312.00752"  # XMM: "https://arxiv.org/abs/2205.01152"

    # # Run the full pipeline
    # audiobook_path, original_text_path, tts_text_path = pipeline.run_pipeline(paper_url, save_text=True)
    # logger.info(f"Full pipeline test completed. Audiobook saved at: {audiobook_path}")
    # logger.info(f"Original text saved at: {original_text_path}")
    # logger.info(f"TTS text saved at: {tts_text_path}")

    # Run individual steps
    logger.info("\nTesting individual steps...")

    # Step 1: Download paper
    arxiv_id, title, paper_text, title_filename, original_text_path = pipeline.download_paper(paper_url, save_text=True)
    logger.info(f"Step 1 completed. Downloaded paper: {title} (arXiv ID: {arxiv_id})")
    logger.info(f"Original text saved at: {original_text_path}")

    # TODO: for testing limit the paper_text length
    paper_text = paper_text[:10000]

    # Step 2: Convert to TTS format
    tts_text, tts_text_path = pipeline.convert_to_tts_format(paper_text, title_filename, save_text=True)
    logger.info("Step 2 completed. Paper converted to TTS format.")
    logger.info(f"TTS text saved at: {tts_text_path}")

    # # Step 3: Convert to audiobook
    # audio_path = pipeline.convert_to_audiobook(tts_text, title_filename)
    # logger.info(f"Step 3 completed. Audiobook created at: {audio_path}")
