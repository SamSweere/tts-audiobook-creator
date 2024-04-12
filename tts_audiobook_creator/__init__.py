import logging
from pathlib import Path

from tts_audiobook_creator.epub_to_text import epub_to_raw_text_book
from tts_audiobook_creator.tts import Audiobook_TTS
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
        self.tts: Audiobook_TTS | None = None
        self.book: dict[str, str | list[dict[str, str]]] = {}

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

    def init_tts(self) -> None:
        if not self.tts:
            self.tts = Audiobook_TTS(
                output_path=self.audiobook_output_dir,
                speaker_path=str(self.config["speaker_path"]),
                language=str(self.config["language"]),
            )

    def read_chapter(self, chapter_index: int) -> Path:
        self.init_tts()

        chapter = self.book["chapters"][chapter_index]

        text = chapter["text"]
        chapter_title = chapter["title"]

        audio_path = self.tts.speak(text, filename=chapter_title)

        return audio_path
