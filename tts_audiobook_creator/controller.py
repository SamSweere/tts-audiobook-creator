import logging
from pathlib import Path

from tqdm import tqdm

from tts_audiobook_creator.epub_to_text import epub_to_raw_text_book
from tts_audiobook_creator.tts import BaseTTS, get_tts
from tts_audiobook_creator.utils import load_config

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


class Audiobook_Controller:
    def __init__(self) -> None:
        self.config = load_config()
        logger.debug(f"Loaded config: {self.config}")

        # Create the output directory if it doesn't exist
        self.output_dir = Path(self.config["output_dir"])  # type: ignore
        self.output_dir.mkdir(exist_ok=True)

        # Initialize the to be used variables
        self.tts: BaseTTS | None = None
        self.book: dict[str, str | list[dict[str, str]]] = {}
        self.audiobook_output_dir: Path = Path()

    def read_book(self, book_path: str | Path) -> None:
        # Read the book
        logger.info(f"Reading book from {book_path}")
        self.book = epub_to_raw_text_book(book_path)
        logger.info(f"Number of chapters: {len(self.book['chapters'])}")

        # Create a directory for the audiobook
        title = str(self.book["title"])
        self.output_dir = Path(self.config["output_dir"])  # type: ignore
        self.audiobook_output_dir = self.output_dir / title
        self.audiobook_output_dir.mkdir(exist_ok=True)
        logger.info(f"Created directory for audiobook: {self.audiobook_output_dir}")

        # Check if there are existing audio files add them if so
        self.get_existing_audio_files()

    def get_existing_audio_files(self) -> None:
        audio_files = list(self.audiobook_output_dir.glob("*.wav"))

        # Update the book with the audio paths
        for audio_file in audio_files:
            chapter_title = audio_file.stem
            for chapter in self.book["chapters"]:
                if chapter["title"] == chapter_title:
                    chapter["audio_path"] = audio_file
                    logger.info(f"Found existing audio file for chapter: {chapter_title}")
                    break

    def init_tts(self) -> None:
        if not self.tts:
            self.tts = get_tts()

    def read_chapter(self, chapter_index: int) -> Path:
        """Read a chapter and save the audio file to the output directory

        Args:
            chapter_index (int): The index of the chapter to read
        """
        self.init_tts()

        chapter = self.book["chapters"][chapter_index]

        text = chapter["body"]
        chapter_title = chapter["title"]

        audio_path = self.tts.speak(text, filename=chapter_title)

        chapter["audio_path"] = audio_path

        return audio_path

    def read_all_chapters(self) -> None:
        """Read all chapters in the book"""
        logger.info("Starting to read all chapters")
        for i in tqdm(range(len(self.book["chapters"]))):
            self.read_chapter(i)
        logger.info("Read all chapters")
