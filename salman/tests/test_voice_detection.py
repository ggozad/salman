import pytest

from salman.voice.detection import VoiceDetector, get_voice_segments
from salman.voice.utils import concat_blobs


@pytest.mark.parametrize("get_test_blobs", ["conversations/1"], indirect=True)
def test_voice_segments(get_test_blobs):
    audio = concat_blobs(get_test_blobs)
    timeline = get_voice_segments(audio)
    assert len(timeline) == 12
    assert round(timeline[0].start, 3) == 0.278
    assert round(timeline[0].end, 3) == 4.160

    vd = VoiceDetector()
    voice_segments = []
    for blob in get_test_blobs:
        voice_segments.extend(vd.add_audio(concat_blobs([blob])))
    voice_segments.extend(vd.finalize())
    timeline = vd.timeline
    assert len(timeline) == 14
    assert len(voice_segments) == 14
    assert round(timeline[0].start, 3) == 0.278
    assert round(timeline[0].end, 3) == 4.244
