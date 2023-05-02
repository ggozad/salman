import asyncio
import uuid

import typer
from pydub import AudioSegment

from salman.voice.recorder import MicRecorder
from salman.workers.voice import end_recording, post_blob, start_recording

app = typer.Typer()


@app.command()
def salman():
    """Salman, the voice assistant"""
    recorder = MicRecorder()

    async def _main():
        count = 0
        uid = uuid.uuid4().hex
        print("Recording")
        await start_recording(uid)
        for blob in recorder.record():
            print(f"Recording {count}")
            audio_segment = AudioSegment(
                blob, sample_width=2, channels=1, frame_rate=16384
            )
            await post_blob(uid, count, audio_segment.export(format="mp4").read())
            if count == 0:
                recorder.close()
            count += 1
        print("Done recording")
        await end_recording(uid)

    asyncio.run(_main())


if __name__ == "__main__":
    app()
