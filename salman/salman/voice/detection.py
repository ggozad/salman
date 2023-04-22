from dataclasses import dataclass

import torchaudio
from pyannote.audio import Pipeline
from pyannote.core import Segment, Timeline
from pydub import AudioSegment

pipeline = Pipeline.from_pretrained(
    "pyannote/voice-activity-detection", use_auth_token=True
)


def get_voice_segments(audio: AudioSegment) -> Timeline:
    """Get voice segments from audio.

    Args:
        audio (AudioSegment): Audio to be processed.

    Returns:
        Timeline: The conversation's timeline.
    """
    waveform, sample_rate = torchaudio.load(audio.export(format="wav"))
    va = pipeline({"waveform": waveform, "sample_rate": sample_rate})
    return va.get_timeline()


@dataclass
class VoiceDetector:
    """
    Helper class to detect voice segments in a stream of audio.
    Use add_audio to add audio to the current audio, then call finalize after
    the stream is finished.

    Attributes:
        audio (AudioSegment): The current audio.
        timeline (Timeline): The conversation's timeline.
        time (float): The current time in seconds.
    """

    audio: AudioSegment = AudioSegment.empty()
    timeline = Timeline()
    time: float = 0

    def add_audio(self, audio: AudioSegment) -> list[AudioSegment]:
        """
        Appends audio to the current audio, then detects voice segments.
        Finally returns the voice segments except the last one, which is
        set as the new audio.
        Args:
            audio (AudioSegment): Audio to be processed.
        Returns:
            timeline (Timeline): The conversation's timeline.
        """

        self.audio += audio
        timeline = get_voice_segments(self.audio)
        complete_audio_segments = []
        if len(timeline) > 0:
            last_segment = timeline[-1]
            new_time = (
                self.time + self.audio[: last_segment.start * 1000].duration_seconds
            )
            complete_audio_segments = [
                self.audio[s.start * 1000 : s.end * 1000] for s in timeline[:-1]
            ]

            self.audio = self.audio[last_segment.start * 1000 :]
            adjusted_timeline = Timeline(
                [Segment(t.start + self.time, t.end + self.time) for t in timeline[:-1]]
            )
            self.time = new_time
            self.timeline = self.timeline.union(adjusted_timeline)
        return complete_audio_segments

    def finalize(self) -> list[AudioSegment]:
        """
        Returns the last voice segment's timeline.
        """
        timeline = get_voice_segments(self.audio)
        complete_audio_segments = [
            self.audio[s.start * 1000 : s.end * 1000] for s in timeline
        ]

        adjusted_timeline = Timeline(
            [Segment(t.start + self.time, t.end + self.time) for t in timeline]
        )
        self.timeline = self.timeline.union(adjusted_timeline)
        return complete_audio_segments
