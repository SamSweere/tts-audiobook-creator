from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
from pathlib import Path


from nltk.tokenize import sent_tokenize
import nltk

nltk.download("punkt")  # Ensure the punkt tokenizer is available


def insert_periods_at_splits(text, max_length):
    """Modify text by inserting periods at splits for long sentences, without adding extra periods before newlines."""
    paragraphs = text.split("\n")
    modified_paragraphs = []

    for paragraph in paragraphs:
        sentences = sent_tokenize(paragraph)
        modified_sentences = []
        for sentence in sentences:
            if len(sentence) > max_length:
                # Recursively split long sentences and insert periods, ensuring proper punctuation
                sentence = split_and_insert_period(sentence, max_length)
            elif not sentence.endswith("."):
                sentence += "."
            modified_sentences.append(sentence)
        # Join the modified sentences, taking care not to add a period if the paragraph was empty
        modified_paragraphs.append(" ".join(modified_sentences))

    # Join the modified paragraphs with newlines, preserving original newline positions
    return "\n".join(modified_paragraphs)


def split_and_insert_period(sentence, max_length):
    """Recursively split a sentence and insert periods, ensuring proper punctuation."""
    if len(sentence) <= max_length:
        return sentence if sentence.endswith(".") else sentence + "."
    else:
        # Attempt to split at a comma or space within the max_length limit
        split_point = sentence.rfind(",", 0, max_length)
        if split_point == -1:  # No comma found, use space as a fallback
            split_point = sentence.rfind(" ", 0, max_length)
        if (
            split_point == -1 or split_point == 0
        ):  # No suitable split point found, or it's at the start
            split_point = max_length
        part1 = sentence[:split_point].strip()
        part2 = (
            sentence[split_point + 1 :].strip()
            if sentence[split_point] == ","
            else sentence[split_point:].strip()
        )

        # Replace a comma with a period if it's the split point, and ensure part1 ends with a period
        part1 = (part1[:-1] if part1.endswith(",") else part1) + "."
        # Recursively process part2
        part2_processed = split_and_insert_period(part2, max_length)
        return part1 + ("" if part2_processed == "." else " " + part2_processed)


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


def epub_to_raw_text_book(epub_path: str | Path, max_sentence_length: int = 300):
    epub_book = epub.read_epub(str(epub_path))

    book = {}

    title = epub_book.get_metadata("DC", "title")[0][0]
    book["title"] = title

    author = epub_book.get_metadata("DC", "creator")[0][0]
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

            # Insert periods at sentence splits
            cleaned_text = insert_periods_at_splits(
                cleaned_text, max_length=max_sentence_length
            )

            chapter["text"] = cleaned_text

            chapters.append(chapter)

    book["chapters"] = chapters
    return book
