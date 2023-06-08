import asyncio
from pathlib import Path

import typer

from salman.app.salman import Salman
from salman.documents.watcher import watch_for_documents

app = typer.Typer()
watcher = typer.Typer()


@app.command()
def salman():
    app = Salman()
    app.run()


@watcher.command()
def doc_watch(paths: list[Path]):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(watch_for_documents(*paths))


if __name__ == "__main__":
    app()
