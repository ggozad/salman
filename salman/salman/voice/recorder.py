import pyaudio

from salman.logging import recorder_logger as logger


class MicRecorder:
    def __init__(self, rate=16384, chunk=16384):
        self.rate = rate
        self.chunk = chunk

    def record(self, duration=5):
        self.p = pyaudio.PyAudio()
        device_name = self.p.get_default_input_device_info().get("name")
        logger.info(f'Recording on device "{device_name}"')
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
        logger.info(f'Stoped recording on device "{device_name}"')

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
