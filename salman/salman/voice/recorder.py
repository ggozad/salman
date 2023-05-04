import asyncio

import pyaudio

from salman.logging import recorder_logger as logger


class MicRecorder:
    def __init__(self, rate=16384, frames_per_buffer=16384):
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.queue = asyncio.Queue()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def start(self):
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue()

        def callback(in_data, frame_count, time_info, status):
            loop.call_soon_threadsafe(self.queue.put_nowait, (in_data[:], status))
            return in_data, pyaudio.paContinue

        self.audio = pyaudio.PyAudio()
        device_name = self.audio.get_default_input_device_info().get("name")
        logger.info(f'Recording on device "{device_name}"')
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
            stream_callback=callback,
        )
        self.stream.start_stream()

    def __aiter__(self):
        return self.record()

    async def record(self):
        try:
            while self.stream.is_active():
                indata, status = await self.queue.get()
                yield indata, status
        except OSError:
            pass

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
