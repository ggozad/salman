import asyncio

import typer

from salman.nats import Session

app = typer.Typer()


@app.command()
def segmentation_worker():
    """Runs the segmentation worker"""
    from salman.workers.voice import segmentation_handler

    asyncio.run(segmentation_handler())


@app.command()
def transcription_worker():
    """Runs the transcription worker"""
    from salman.workers.voice import transcription_handler

    asyncio.run(transcription_handler())


@app.command()
def cleanup_worker():
    """Runs the cleanup worker"""
    from salman.workers.voice import cleanup_handler

    asyncio.run(cleanup_handler())


@app.command()
def setup():
    """Setup streams and KV stores"""
    from salman.config import Config
    from salman.workers.voice import SUBJECTS

    async def _main():
        async with Session(Config.NATS_URL) as mgr:
            await mgr.delete_stream(Config.VOICE_STREAM)
            await mgr.add_stream(Config.VOICE_STREAM, SUBJECTS)

    asyncio.run(_main())


if __name__ == "__main__":
    app()
