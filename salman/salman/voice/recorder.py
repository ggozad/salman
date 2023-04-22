import pyaudio


class MicRecorder:
    def __init__(self, rate=16384, chunk=16384):
        self.rate = rate
        self.chunk = chunk

    def record(self, duration=5):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )
        self.stream.start_stream()
        try:
            while self.stream.is_active():
                yield self.stream.read(duration * self.chunk)
        except OSError:
            pass

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
