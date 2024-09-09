import re

from pydub import AudioSegment
from tqdm import tqdm


def stitch_audio(audio_files, output_file):
    print("Stitching audio files together...")
    combined = AudioSegment.empty()
    for audio_file in tqdm(audio_files, desc="Combining audio"):
        segment = AudioSegment.from_file(audio_file, format="mp3")
        combined += segment
    print(f"Exporting final audio to {output_file}")
    combined.export(output_file, format="mp3")


def split_text(text, max_chars=4000):
    print("Splitting text into chunks...")
    sentences = re.split("(?<=[.!?]) +", text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    print(f"Text split into {len(chunks)} chunks")
    return chunks
