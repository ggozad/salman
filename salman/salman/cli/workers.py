import asyncio
from pathlib import Path

import typer

from salman.workers.voice import post_blob, conversation_handler, end_recording

app = typer.Typer()


@app.command()
def add_blob(
    file: str = typer.Argument(..., help="The file to add to the queue"),
    recording_id: str = typer.Argument(..., help="The recording id"),
    index: int = typer.Argument(..., help="The index of the blob"),
    final: bool = typer.Option(False, help="Is this the final blob?"),
):
    """Add a blob to the queue."""
    blob = Path(file)
    data = blob.read_bytes()
    asyncio.run(post_blob(recording_id, index, data))
    if final:
        asyncio.run(end_recording(recording_id))


@app.command()
def conversation_worker():
    """Add a blob to the queue."""
    asyncio.run(conversation_handler())


if __name__ == "__main__":
    app()
