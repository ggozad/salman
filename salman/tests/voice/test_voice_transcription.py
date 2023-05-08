import pytest

from salman.voice.detection import VoiceDetector, get_voice_segments
from salman.voice.transcription import transcribe_segment
from salman.voice.utils import concat_blobs


@pytest.mark.parametrize("get_test_blobs", ["conversations/1"], indirect=True)
def test_trasncribe_blob_batches(get_test_blobs):
    audio = concat_blobs(get_test_blobs)
    res = transcribe_segment(audio)

    assert res.get("language") == "en"
    assert res.get("text") == (
        " No, not suddenly. For a while she was translating movie subtitles. Kind of "
        "a dead-end job? Yes, she got really tired of it. She couldn't see any future "
        "in it. It didn't pay all that well either. And we needed yesterday deadlines "
        "for killing her. So then? She started writing her own songs and performing "
        "them in pubs accompanying herself on the guitar. Later she added some more "
        "instrumentalists. She has a nice voice and the lyrics are really thoughtful. "
        "She's just put out her second CD. I can get you one if you want. That would "
        "be great. I'll show it off to everybody and tell them I know somebody who "
        "knows somebody famous."
    )


@pytest.mark.parametrize("get_test_blobs", ["conversations/1"], indirect=True)
def test_transcribe_voice_activated_segments(get_test_blobs):
    audio = concat_blobs(get_test_blobs)
    timeline = get_voice_segments(audio)
    segment = timeline[0]
    transcription = transcribe_segment(audio[segment.start * 1000 : segment.end * 1000])
    assert transcription.get("language") == "en"
    assert transcription.get("text") == (
        " No, not suddenly. For a while she was translating movie subtitles."
    )

    segment = timeline[-1]
    transcription = transcribe_segment(audio[segment.start * 1000 : segment.end * 1000])
    assert transcription.get("language") == "en"
    assert transcription.get("text") == (
        " That would be great. I'll show it off to everybody and tell them I know somebody who knows somebody famous."
    )


@pytest.mark.parametrize("get_test_blobs", ["conversations/1"], indirect=True)
def test_transcribe_voice_detector_segments(get_test_blobs):
    vd = VoiceDetector()
    voice_segments = []
    for blob in get_test_blobs:
        voice_segments.extend(vd.add_audio(concat_blobs([blob])))
    voice_segments.extend(vd.finalize())
    assert len(voice_segments) == 14
    transcription = transcribe_segment(voice_segments[0])
    assert transcription.get("language") == "en"
    assert (
        transcription.get("text")
        == " No, not suddenly. For a while she was translating movie subtitles."
    )
    transcription = transcribe_segment(voice_segments[-1])
    assert transcription.get("language") == "en"
    assert (
        transcription.get("text")
        == " I'll show it off to everybody and tell them I know somebody who knows somebody famous."
    )
