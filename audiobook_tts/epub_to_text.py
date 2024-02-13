from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
from pathlib import Path


def clean_html_content(element):
    """
    Recursively convert an HTML element to plain text with minimal newlines,
    adding newlines only after block-level elements.
    """
    text_parts = []
    if element.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "li"]:
        # Block-level elements that should have newlines before and after
        text_parts.append("\n")  # Add newline before the block element
        if element.string:
            text_parts.append(element.string)
        else:
            for content in element.contents:
                text_parts.append(clean_html_content(content))
        text_parts.append("\n")  # Add newline after the block element
    elif element.name in ["br", "hr"]:
        # Elements that represent breaks
        text_parts.append("\n")
    elif element.name is None:
        # NavigableString or similar
        text_parts.append(element.strip())
    else:
        # Inline elements or elements whose content should be directly concatenated
        if element.string:
            text_parts.append(element.string.strip())
        else:
            for content in element.contents:
                text_parts.append(clean_html_content(content))
    
    return "".join(text_parts)


def epub_to_raw_text_book(epub_path: str | Path):
    epub_book = epub.read_epub(str(epub_path))

    book = {}

    title = epub_book.get_metadata('DC', 'title')[0][0]
    book["title"] = title

    author = epub_book.get_metadata('DC', 'creator')[0][0]
    book["author"] = author

    chapters = []
    for item in epub_book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapter = {}

            chapter_name = item.get_name().split("/")[-1].split(".")[0]

            chapter["name"] = chapter_name

            xhtml_content = item.get_body_content()

            # Decode bytes to string and parse with BeautifulSoup
            soup = BeautifulSoup(xhtml_content.decode("utf-8"), "lxml")

            # Now using the custom function to clean the HTML content
            cleaned_text = clean_html_content(soup)

            # Remove starting and trailing newlines
            cleaned_text = cleaned_text.strip()

            chapter["text"] = cleaned_text

            chapters.append(chapter)

    book["chapters"] = chapters
    return book
