import logging
from pathlib import Path

import gradio as gr

from tts_audiobook_creator.controller.audiobook_controller import Audiobook_Controller

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class AudioBookCreatorUI:
    def __init__(self, controller) -> None:
        self.controller = controller

        # We need to define a maximum number of audio previews to show
        # since we have to initialize the audio blocks with a fixed number we set them to invisible initially
        self.max_preview_audios = 100

        # Store chapters and titles as instance variables
        self.chapters: list[dict[str, str]] = []
        self.chapter_titles: list[str] = []

        self.interface = gr.Blocks()
        # Set up the Gradio interface within the class
        with self.interface:
            title = gr.Markdown("# TTS AudioBook Creator", label="Title")  # noqa
            with gr.Row():
                with gr.Column(scale=1, min_width=600):
                    # Column 1 contains the file upload, chapter selection dropdown, and chapter content textfield
                    file_input = gr.File(label="Upload Epub File", file_types=["epub"])
                    chapters_dropdown = gr.Dropdown(
                        choices=self.chapter_titles,
                        type="index",
                        multiselect=False,
                        label="Chapter Selection",
                        interactive=True,
                    )
                    chapter_body_textbox = gr.Textbox(lines=10, interactive=False, show_label=False)
                    generate_audio_button = gr.Button("Generate Audio")
                    # generate_whole_book_button = gr.Button("Generate Whole Book")

                with gr.Column(scale=1, min_width=600):
                    # Column 2 contains the audio preview blocks
                    # tmp_update_button = gr.Button("TMP Update Audio Blocks")
                    audioboxes = []
                    for _ in range(self.max_preview_audios):
                        audioboxes.append(gr.Audio(label="Invisible Placeholder", visible=False))

            # Process the file and update the chapter dropdown and content textfield when a file is uploaded
            file_input.upload(
                self.process_upload,
                inputs=file_input,
                outputs=[chapters_dropdown, chapter_body_textbox, *audioboxes],
            )

            # Update the chapter content textfield when a chapter is selected
            chapters_dropdown.select(
                fn=self.chapter_dropdown_update, inputs=chapters_dropdown, outputs=chapter_body_textbox
            )

            # Generate audio for the selected chapter when the button is clicked
            # and update the audio preview blocks
            # TODO: Update only one audio block instead of all
            generate_audio_button.click(
                self.generate_audio, inputs=[chapters_dropdown, chapter_body_textbox], outputs=audioboxes
            )

            # Update the chapter body when the textfield is changed
            chapter_body_textbox.change(self.update_chapter_text, inputs=[chapters_dropdown, chapter_body_textbox])

    def update_chapter_text(self, chapter_index: int, text_body: str) -> None:
        logger.info(f"Updating chapter {chapter_index} with: {text_body}")
        self.chapters[chapter_index]["body"] = text_body

    def update_chapter_audio_blocks(self) -> list[gr.Audio]:
        audioboxes = []

        # We iterate through the chapters in order such that the audio blocks are in the correct order
        for _, chapter in enumerate(self.chapters):
            if "audio_path" in chapter:
                logger.debug(f"Adding audio block for: {chapter['audio_path']}")
                audioboxes.append(gr.Audio(chapter["audio_path"], label=chapter["title"], visible=True))
            else:
                logger.debug(f"No audio block for: {chapter['title']}")
                audioboxes.append(gr.Audio(label="Invisible Placeholder", visible=False))

        # Add invisible placeholders for the remaining audio blocks
        for _ in range(self.max_preview_audios - len(self.chapters)):
            audioboxes.append(gr.Audio(label="Invisible Placeholder", visible=False))

        return audioboxes

    # TODO: Update only one audio block instead of all
    # def update_single_audio_block(self, chapter_index: int) -> gr.Audio:
    #     chapter = self.chapters[chapter_index]
    #     if "audio_path" in chapter:
    #         logger.debug(f"Adding audio block for: {chapter['audio_path']}")
    #         return gr.Audio(chapter["audio_path"], label=chapter["title"], visible=True)
    #     else:
    #         logger.debug(f"No audio block for: {chapter['title']}")
    #         return gr.Audio(label="Invisible Placeholder", visible=False)

    def generate_audio(self, chapter_index: int, chapter_content: str) -> Path:
        chapter_title = self.chapters[chapter_index]["title"]
        logger.info(f"Generating audio for chapter {chapter_title}. With content: {chapter_content}")

        # Let the controller read the chapter
        self.controller.read_chapter(chapter_index)

        # Update the audio blocks
        return self.update_chapter_audio_blocks()

    def chapter_dropdown_update(self, i: int) -> gr.Textbox:
        return gr.Textbox(value=self.chapters[i]["body"], interactive=True)

    def process_upload(self, fileobj: gr.File) -> tuple[gr.Dropdown, gr.Textbox]:
        logger.info(f"Processing file: {fileobj.name}")

        # Read the book
        self.controller.read_book(fileobj.name)

        # Store the chapters and titles
        self.chapters = self.controller.book["chapters"]
        self.chapter_titles = [chapter["title"] for chapter in self.chapters]

        logger.info(f"{self.chapter_titles=}")
        return [
            gr.Dropdown(
                choices=self.chapter_titles,
                value=self.chapter_titles[0],
                type="index",
                multiselect=False,
                label="Chapter Selection",
                interactive=True,
            ),
            self.chapters[0]["body"],
        ] + self.update_chapter_audio_blocks()

    def launch(self) -> None:
        # Method to launch the Gradio interface
        self.interface.launch()


# # Example of how to use the class
# if __name__ == "__main__":
# For interactive development remove the `if __name__ == "__main__":` block
# and run: `gradio tts_audiobook_creator/ui.py`
# Instantiate the controller
controller = Audiobook_Controller()
ui = AudioBookCreatorUI(controller)
demo = ui.interface
ui.launch()
