import logging

from tts_audiobook_creator.controller.audiobook_controller import Audiobook_Controller

logging.basicConfig(level=logging.WARNING)

# Instantiate the controller
controller = Audiobook_Controller()

# Read the book
config = controller.config
book_path = config["book_path"]

controller.read_book(book_path)

# Read the first chapter
audio_path = controller.read_chapter(0)

# Read all chapters
controller.read_all_chapters()
