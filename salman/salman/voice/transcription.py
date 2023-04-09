import tempfile

import whisper
from pydub import AudioSegment

model = whisper.load_model("base")


def transcribe_segment(audio: AudioSegment) -> dict:
    """
    Transcribe audio segment.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav") as file:
        file.write(audio.export(format="wav").read())
        transcription = model.transcribe(file.name)

    return transcription
