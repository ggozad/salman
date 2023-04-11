import asyncio
from pathlib import Path

import typer

from salman.workers.voice import post_blob

app = typer.Typer()


@app.command()
def add_blob(file: str = typer.Argument(..., help="The file to add to the queue")):
    """Add a blob to the queue."""
    blob = Path(file)
    data = blob.read_bytes()
    # post_blob(blob.name, 0, data)

    asyncio.run(post_blob("conv_id", 0, data))


if __name__ == "__main__":
    app()
