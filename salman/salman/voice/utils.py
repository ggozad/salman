from io import BytesIO

from pydub import AudioSegment


def concat_blobs(blobs: list[bytes]) -> AudioSegment:
    """
    Concatenate audio blobs into a single AudioSegment."""
    audio = AudioSegment.empty()
    for blob in blobs:
        audio += AudioSegment.from_file(BytesIO(blob), "mp4")
    return audio
