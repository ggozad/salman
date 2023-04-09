import asyncio

import typer

from salman.nats.workers import subscribe as _subscribe
from salman.nats.workers import publish as _publish

app = typer.Typer()


@app.command()
def subscribe(stream: str, subject: str, queue: str = None):
    async def cb(msg):
        print(msg)
        await msg.ack()

    async def _main():
        await _subscribe(stream, subject, cb, queue=queue)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main())
    loop.run_forever()
    loop.close()


@app.command()
def publish(subject: str, body: str):
    async def _main():
        await _publish(subject, body)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main())
    loop.close()


if __name__ == "__main__":
    app()
