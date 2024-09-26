import logging
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from tts_audiobook_creator.utils import get_project_root_path

logger = logging.getLogger(__name__)


def extract_arxiv_id(arxiv_url: str) -> str:
    """
    Extract the arXiv ID from a given arXiv URL.

    Args:
        arxiv_url (str): The URL of the arXiv paper.

    Returns:
        str: The arXiv ID.

    Raises:
        ValueError: If the URL is not a valid arXiv URL.
    """
    parsed_url = urlparse(arxiv_url)
    if parsed_url.netloc != "arxiv.org":
        raise ValueError("The URL must be from arXiv.")

    path_parts = parsed_url.path.split("/")
    arxiv_id = path_parts[-1]
    if not arxiv_id:
        arxiv_id = path_parts[-2]  # Handle URLs ending with a slash

    if not arxiv_id or "." not in arxiv_id:
        raise ValueError("Unable to extract a valid arXiv ID from the URL.")

    return arxiv_id


def fetch_arxiv_title(arxiv_id: str) -> str:
    """
    Fetch the title of an arXiv paper using the arXiv API.

    Args:
        arxiv_id (str): The arXiv ID of the paper.

    Returns:
        str: The title of the paper.

    Raises:
        requests.RequestException: If there's an error fetching the data from the API.
        ValueError: If the API response is not in the expected format.
    """
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()

        # Parse the XML response
        root = ET.fromstring(response.content)

        # Define the namespace
        namespace = {"atom": "http://www.w3.org/2005/Atom"}

        # Find the title element within the entry
        title_element = root.find(".//atom:entry/atom:title", namespaces=namespace)

        if title_element is not None and title_element.text:
            # Clean up the title: remove newlines and extra spaces
            title = " ".join(title_element.text.split())
            return title
        else:
            logger.warning(f"Could not find title for arXiv ID: {arxiv_id}")
            return "Unknown Title"

    except requests.RequestException as e:
        logger.error(f"Error fetching arXiv data: {e}")
        raise
    except ET.ParseError as e:
        logger.error(f"Error parsing arXiv API response: {e}")
        raise ValueError("Invalid API response format") from e


def fetch_arxiv_latex_archive(arxiv_url: str) -> Path:
    """
    Fetch the LaTeX archive of an arXiv paper.

    Args:
        arxiv_url (str): The URL of the arXiv paper.

    Returns:
        Path: The path to the downloaded LaTeX archive.

    Raises:
        ValueError: If the URL is not from arXiv.
        requests.RequestException: If there's an error downloading the file.
    """
    logger.info(f"Fetching arXiv paper from {arxiv_url}...")

    paper_id = extract_arxiv_id(arxiv_url)
    source_url = f"https://arxiv.org/src/{paper_id}"
    temp_dir = get_project_root_path() / "data" / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    archive_path = temp_dir / f"{paper_id}.tar.gz"

    if archive_path.exists():
        logger.info("Paper archive already downloaded.")
        return archive_path

    response = requests.get(source_url, stream=True)
    response.raise_for_status()
    with open(archive_path, "wb") as archive_file:
        shutil.copyfileobj(response.raw, archive_file)
    logger.info("Download complete.")
    return archive_path


def extract_latex_archive(archive_path: Path) -> Path:
    """
    Extract a LaTeX archive file.

    Args:
        archive_path (Path): The path to the LaTeX archive file.

    Returns:
        Path: The path to the extracted directory.

    Raises:
        shutil.ReadError: If there's an error extracting the archive.
    """
    extracted_dir = archive_path.with_suffix("").with_suffix("")  # Remove the .tar.gz extension
    extracted_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Extracting LaTeX archive {archive_path} to {extracted_dir}...")

    shutil.unpack_archive(archive_path, extracted_dir)
    logger.info("Extraction complete.")
    return extracted_dir


def find_main_latex_content(latex_dir: Path) -> str:
    """
    Find and read the main LaTeX file in the extracted arXiv paper directory.

    Args:
        latex_dir (Path): The path to the extracted arXiv paper directory.

    Returns:
        str: The content of the main LaTeX file.

    Raises:
        FileNotFoundError: If the main LaTeX file is not found.
    """
    tex_files = list(latex_dir.glob("*.tex"))
    main_tex_file = next(
        (tex_file for tex_file in tex_files if tex_file.read_text().startswith("\\documentclass")), None
    )

    if main_tex_file is None:
        logger.error("Could not find the main LaTeX file.")
        raise FileNotFoundError("Main LaTeX file not found in the extracted directory.")

    logger.info(f"Found main LaTeX file: {main_tex_file}")
    return main_tex_file.read_text()


def process_arxiv_latex_paper(arxiv_url: str) -> (str, str):
    """
    Process an arXiv paper: fetch, extract, and get the LaTeX content.

    Args:
        arxiv_url (str): The URL of the arXiv paper.

    Returns:
        tuple[str, str]: A tuple containing the LaTeX content and the paper title.

    Raises:
        ValueError: If the URL is not from arXiv or the arXiv ID can't be extracted.
        requests.RequestException: If there's an error downloading the file.
        shutil.ReadError: If there's an error extracting the archive.
        FileNotFoundError: If the main LaTeX file is not found.
    """
    arxiv_id = extract_arxiv_id(arxiv_url)
    title = fetch_arxiv_title(arxiv_id)

    # Fetch and process the LaTeX content (reusing existing functions)
    archive_path = fetch_arxiv_latex_archive(arxiv_url)
    extracted_dir = extract_latex_archive(archive_path)
    latex_content = find_main_latex_content(extracted_dir)

    return latex_content, title


def fetch_arxiv_html(arxiv_url) -> str:
    """
    Fetch the HTML content of an arXiv paper given its URL.

    Args:
        arxiv_url (str): The URL of the arXiv paper.

    Returns:
        str: The HTML content of the paper.

    Raises:
        requests.RequestException: If there's an error downloading the HTML page.
    """
    paper_id = extract_arxiv_id(arxiv_url)
    html_url = f"https://arxiv.org/html/{paper_id}v2"

    # Download the HTML page
    response = requests.get(html_url)

    if response.status_code == 200:
        return response.text
    else:
        raise requests.RequestException(f"Failed to download HTML page. Status code: {response.status_code}")


def extract_main_html_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    # Find the main title
    main_title = soup.find("h1", class_="ltx_title ltx_title_document")

    if main_title:
        # Start from the main title and get all following siblings
        content = [str(main_title)]
        for sibling in main_title.next_siblings:
            content.append(str(sibling))

        return "".join(content)
    else:
        return "Main content not found"


def clean_html_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # List of allowed tags
    allowed_tags = [
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "strong",
        "em",
        "u",
        "a",
        "ul",
        "ol",
        "li",
        "table",
        "tr",
        "td",
        "th",
        "caption",
        "math",
        "sub",
        "sup",
        "img",
        "figure",
        "figcaption",
    ]

    # Attributes to keep for specific tags
    keep_attributes = {
        "a": ["href"],
        "img": ["src", "alt"],
        "math": ["alttext"],
        "td": ["rowspan", "colspan"],
        "th": ["rowspan", "colspan"],
    }

    for tag in soup.find_all():
        if tag.name not in allowed_tags:
            tag.unwrap()
        else:
            # Keep only specific attributes for allowed tags
            allowed_attrs = keep_attributes.get(tag.name, [])
            tag.attrs = {attr: tag[attr] for attr in allowed_attrs if attr in tag.attrs}

    # Special handling for math content
    for math_tag in soup.find_all("math"):
        math_content = math_tag.get("alttext", "")
        math_tag.string = f"[MATH: {math_content}]"

    # Remove empty tags
    for tag in soup.find_all():
        if len(tag.get_text(strip=True)) == 0 and tag.name not in ["img", "br"]:
            tag.extract()

    # Clean up whitespace
    cleaned_html = re.sub(r"\s+", " ", str(soup))
    cleaned_html = re.sub(r"> <", "><", cleaned_html)

    return cleaned_html


def process_arxiv_html_paper(arxiv_url: str) -> (str, str):
    """
    Process an arXiv HTML paper: fetch, extract, and get the HTML content.

    Args:
        arxiv_url (str): The URL of the arXiv paper.

    Returns:
        tuple[str, str]: A tuple containing the HTML content and the paper title.

    Raises:
        ValueError: If the URL is not from arXiv or the arXiv ID can't be extracted.
        requests.RequestException: If there's an error downloading the html
    """
    arxiv_id = extract_arxiv_id(arxiv_url)
    title = fetch_arxiv_title(arxiv_id)

    html_text = fetch_arxiv_html(arxiv_url)
    html_text = extract_main_html_content(html_text)
    html_text = clean_html_content(html_text)

    return html_text, title


if __name__ == "__main__":
    # sample_arxiv_url = "https://arxiv.org/abs/2205.01152" # XMM
    sample_arxiv_url = "https://arxiv.org/abs/2312.00752"  # Mamba
    # latex_content, paper_title = process_arxiv_latex_paper(sample_arxiv_url)
    latex_content, paper_title = process_arxiv_html_paper(sample_arxiv_url)
    print(f"Paper Title: {paper_title}")
    print("First 500 characters of LaTeX content:")
    print(latex_content[:500])
