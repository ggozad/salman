import asyncio
from pathlib import Path

import typer

from salman.nats import NATSManager
from salman.workers.voice import end_recording, post_blob, recording_handler

app = typer.Typer()


@app.command()
def add_blob(
    file: str = typer.Argument(..., help="The file to add to the queue"),
    index: int = typer.Argument(..., help="The index of the blob"),
    recording_id: str = typer.Option(None, help="The recording id"),
    final: bool = typer.Option(False, help="Is this the final blob?"),
):
    """Add a blob to the queue."""
    blob = Path(file)
    data = blob.read_bytes()
    if recording_id is None:
        recording_id = "test"
    asyncio.run(post_blob(recording_id, index, data))
    if final:
        asyncio.run(end_recording(recording_id))


@app.command()
def conversation_worker():
    """Add a blob to the queue."""
    asyncio.run(recording_handler())


@app.command()
def setup():
    """Setup streams and KV stores"""
    from salman.workers.voice import SUBJECTS as voice_SUBJECTS  # noqa F401
    from salman.workers.voice import STREAM as voice_STREAM  # noqa F401

    async def _main():
        mgr = await NATSManager().create()
        await mgr.delete_stream(voice_STREAM)
        await mgr.add_stream(voice_STREAM, voice_SUBJECTS)
        await mgr.delete_kv_bucket("voice")
        await mgr.delete_kv_bucket("blobs-test")
        await mgr.delete_kv_bucket("recording-test")
        await mgr.delete_kv_bucket("segments-test")

    asyncio.run(_main())


if __name__ == "__main__":
    app()
