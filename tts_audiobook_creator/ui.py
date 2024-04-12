import gradio as gr


class AudioBookCreatorUI:
    def __init__(self) -> None:
        # Store chapters and titles as instance variables
        self.chapters: list[dict[str, str]] = []
        self.chapter_titles: list[str] = []

        # Set up the Gradio interface within the class
        with gr.Blocks() as demo:
            title = gr.Markdown("# TTS AudioBook Creator", label="Title")  # noqa
            with gr.Row():
                with gr.Column(scale=1, min_width=600):
                    self.file_input = gr.File(label="Upload File")

                with gr.Column(scale=1, min_width=600):
                    self.chapters_dropdown = gr.Dropdown(
                        choices=self.chapter_titles,
                        type="index",
                        multiselect=False,
                        label="Main Dropdown",
                        interactive=True,
                    )
                    self.chapter_content = gr.Textbox(label="Chapter Text", lines=10, interactive=False)

            self.file_input.upload(
                self.process_upload, inputs=self.file_input, outputs=[self.chapters_dropdown, self.chapter_content]
            )
            self.chapters_dropdown.select(
                fn=self.rs_change, inputs=self.chapters_dropdown, outputs=self.chapter_content
            )

        self.demo = demo

    def extract_chapters(self, fileobj: gr.File) -> list[dict[str, str]]:
        with open(fileobj.name) as f:
            text = f.read()
        chapter_contents = text.split("Chapter")[1:]  # Assuming each chapter starts with 'Chapter'
        chapters = []
        for chapter_content in chapter_contents:
            chapter = {
                "title": "Chapter " + chapter_content.split("\n")[0],
                "content": chapter_content.strip(),  # Remove leading/trailing whitespaces
            }
            chapters.append(chapter)
        return chapters

    def rs_change(self, i: int) -> gr.Textbox:
        return gr.Textbox(value=self.chapters[i]["content"], interactive=True)

    def process_upload(self, fileobj: gr.File) -> tuple[gr.Dropdown, gr.Textbox]:
        print(f"Processing file: {fileobj.name}")
        self.chapters = self.extract_chapters(fileobj)
        self.chapter_titles = [chapter["title"] for chapter in self.chapters]
        print(f"{self.chapter_titles=}")
        return gr.Dropdown(
            choices=self.chapter_titles,
            value=self.chapter_titles[0],
            type="index",
            multiselect=False,
            label="Main Dropdown",
            interactive=True,
        ), self.chapters[0]["content"]

    def launch(self) -> None:
        # Method to launch the Gradio interface
        self.demo.launch()


# Example of how to use the class
if __name__ == "__main__":
    ui = AudioBookCreatorUI()
    ui.launch()
