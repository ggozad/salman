import tempfile

import whisper
from pydub import AudioSegment

model = whisper.load_model("base")


def transcribe_segment(audio: AudioSegment) -> dict:
    """
    Transcribe audio segment.
    """

    # This should happen without dumping to disk by converting
    # to an numpy array and passing that to the model.
    # See https://github.com/openai/whisper/blob/main/whisper/audio.py
    with tempfile.NamedTemporaryFile(suffix=".wav") as file:
        file.write(audio.export(format="wav").read())
        transcription = model.transcribe(file.name)

    return transcription
