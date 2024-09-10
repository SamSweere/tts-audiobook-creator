import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

from tts_audiobook_creator.arxiv import extract_arxiv_id, process_arxiv_paper
from tts_audiobook_creator.tts import BaseTTS, get_tts
from tts_audiobook_creator.utils import load_config

logger = logging.getLogger(__name__)


class ArxivController:
    def __init__(self) -> None:
        """Initialize the ArxivController."""
        self.config: dict[str, Any] = load_config()
        logger.debug(f"Loaded config: {self.config}")

        # Create the output directory if it doesn't exist
        self.output_dir: Path = Path(self.config["output_dir"])
        self.output_dir.mkdir(exist_ok=True)

        # Initialize the TTS engine
        self.tts: BaseTTS = get_tts()

        # Initialize variables to store paper information
        self.arxiv_id: str = None
        self.paper_text: str = None
        self.title: str = None
        self.max_filename_length = 50
        self.title_filename: str = None
        self.audiobook_output_dir: Path = Path()
        self.audio_output_path: Path = Path()

    def _create_title_filename(self) -> None:
        """Create a filename-friendly version of the paper title."""
        if not self.title:
            raise ValueError("No paper title available.")

        def clean_filename(filename):
            # Remove or replace illegal characters
            filename = re.sub(r'[<>:"/\\|?*]', "", filename)
            filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

            # Replace spaces and periods with underscores
            filename = re.sub(r"[\s.]+", "_", filename)

            # Remove control characters
            filename = "".join(ch for ch in filename if unicodedata.category(ch)[0] != "C")

            # Normalize Unicode characters
            filename = unicodedata.normalize("NFKD", filename).encode("ASCII", "ignore").decode("ASCII")

            # Remove leading/trailing periods and spaces
            filename = filename.strip(". ")

            return filename

        # Clean and create initial filename
        filename = clean_filename(self.title)

        # Ensure max_filename_length is at least 1
        max_length = max(1, self.max_filename_length)

        # Split the filename into parts
        parts = filename.split("_")

        # Initialize the result
        result = []
        current_length = 0

        # Add parts while respecting the maximum length
        for part in parts:
            if current_length + len(part) + (1 if result else 0) <= max_length:
                if result:
                    current_length += 1  # Account for the underscore
                result.append(part)
                current_length += len(part)
            else:
                break

        # If no parts fit, take the first max_length characters of the first part
        if not result:
            result = [filename[:max_length]]

        # Join the parts that fit within the maximum length
        self.title_filename = "_".join(result)

        # Ensure the filename is not empty and doesn't start with a period
        if not self.title_filename or self.title_filename.startswith("."):
            self.title_filename = "untitled" + (self.title_filename if self.title_filename else "")

    def download_paper(self, arxiv_url: str) -> None:
        """
        Download the arXiv paper and extract its text.

        Args:
            arxiv_url (str): The URL of the arXiv paper.
        """
        logger.info(f"Downloading arXiv paper from {arxiv_url}...")
        self.arxiv_id = extract_arxiv_id(arxiv_url)
        self.paper_text, self.title = process_arxiv_paper(arxiv_url)

        # Create a filename-friendly version of the title
        self._create_title_filename()

        logger.info("Paper downloaded and processed successfully.")

    def save_paper_to_file(self, file_path: Path | None = None) -> None:
        """
        Save the downloaded paper text to a file.

        Args:
            file_path (Optional[Path]): The path to save the file. If None, a default path is used.
        """
        if not self.title_filename or not self.paper_text:
            raise ValueError("No paper has been downloaded yet.")

        if file_path is None:
            self.audiobook_output_dir = self.output_dir / self.title_filename
            self.audiobook_output_dir.mkdir(exist_ok=True)
            file_path = self.audiobook_output_dir / f"{self.title_filename}.tex"

        logger.info(f"Saving the text to {file_path}")

        with open(file_path, "w") as text_file:
            text_file.write(self.paper_text)
        logger.info("Paper text saved to file successfully.")

    def convert_to_audiobook(self) -> None:
        """Convert the paper text to an audiobook."""
        if not self.paper_text:
            raise ValueError("No paper text available. Please download a paper first.")

        self.audiobook_output_dir = self.output_dir / self.title_filename
        self.audiobook_output_dir.mkdir(exist_ok=True)
        self.audio_output_path = self.audiobook_output_dir / f"{self.title_filename}.mp3"
        logger.info(f"Converting the text to an audiobook: {self.audio_output_path}")

        self.tts.speak(self.paper_text, self.audio_output_path)
        logger.info("Audiobook created successfully.")

    def arxiv_to_audiobook(self, arxiv_url: str, save_text: bool = False) -> None:
        """
        Process an arXiv paper: download, optionally save to file, and convert to audiobook.

        Args:
            arxiv_url (str): The URL of the arXiv paper.
            save_text (bool): Whether to save the paper text to a file. Defaults to False.
        """
        self.download_paper(arxiv_url)

        if save_text:
            self.save_paper_to_file()

        self.convert_to_audiobook()
        logger.info(f"arXiv paper {self.arxiv_id} processed and converted to audiobook successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    arxiv_controller = ArxivController()
    arxiv_controller.arxiv_to_audiobook("https://arxiv.org/abs/2205.01152", save_text=True)
