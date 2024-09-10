import logging
from pathlib import Path

from tqdm import tqdm

from tts_audiobook_creator.epub_to_text import epub_to_raw_text_book
from tts_audiobook_creator.tts import BaseTTS, get_tts
from tts_audiobook_creator.utils import load_config

logger = logging.getLogger(__name__)


class AudiobookController:
    def __init__(self) -> None:
        """Initialize the AudiobookController."""
        self.config = load_config()
        logger.debug(f"Loaded config: {self.config}")

        # Create the output directory if it doesn't exist
        self.output_dir = Path(self.config["output_dir"])
        self.output_dir.mkdir(exist_ok=True)

        # Initialize the to be used variables
        self.tts: BaseTTS | None = None
        self.book: dict[str, str | list[dict[str, str]]] = {}
        self.audiobook_output_dir: Path = Path()

    def arxiv_to_audiobook(self, arxiv_url: str) -> None:
        """Convert an arXiv paper to an audiobook."""
        pass

    def read_book(self, book_path: str | Path) -> None:
        """
        Read a book and prepare it for audio conversion.

        Args:
            book_path (Union[str, Path]): The path to the book file.
        """
        # Read the book
        logger.info(f"Reading book from {book_path}")
        self.book = epub_to_raw_text_book(book_path)
        logger.info(f"Number of chapters: {len(self.book['chapters'])}")

        # Create a directory for the audiobook
        title = str(self.book["title"])
        self.audiobook_output_dir = self.output_dir / title
        self.audiobook_output_dir.mkdir(exist_ok=True)
        logger.info(f"Created directory for audiobook: {self.audiobook_output_dir}")

        # Check if there are existing audio files and add them if so
        self.get_existing_audio_files()

    def get_existing_audio_files(self) -> None:
        """Check for existing audio files and update the book accordingly."""
        audio_files = list(self.audiobook_output_dir.glob("*.wav"))

        # Update the book with the audio paths
        for audio_file in audio_files:
            chapter_title = audio_file.stem
            for chapter in self.book["chapters"]:
                if chapter["title"] == chapter_title:
                    chapter["audio_path"] = str(audio_file)
                    logger.info(f"Found existing audio file for chapter: {chapter_title}")
                    break

    def init_tts(self) -> None:
        """Initialize the TTS engine if it hasn't been initialized yet."""
        if not self.tts:
            self.tts = get_tts()

    def read_chapter(self, chapter_index: int) -> Path:
        """
        Read a chapter and save the audio file to the output directory.

        Args:
            chapter_index (int): The index of the chapter to read.

        Returns:
            Path: The path to the generated audio file.
        """
        self.init_tts()
        chapter = self.book["chapters"][chapter_index]
        text = chapter["body"]
        chapter_title = chapter["title"]
        output_file_path = self.audiobook_output_dir / f"{chapter_title}.wav"

        audio_path = self.tts.speak(text, output_file_path)
        chapter["audio_path"] = str(audio_path)
        return audio_path

    def read_all_chapters(self) -> None:
        """Read all chapters in the book."""
        logger.info("Starting to read all chapters")
        for i in tqdm(range(len(self.book["chapters"]))):
            self.read_chapter(i)
        logger.info("Read all chapters")


# if __name__ == "__main__":
#     # Example usage
#     controller = AudiobookController()
#     controller.read_book("path/to/your/book.epub")
#     controller.read_all_chapters()
