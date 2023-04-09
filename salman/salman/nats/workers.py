import asyncio
import signal

import nats

from salman.config import Config


def _handle_signals(client: nats.aio.client.Client):
    async def stop():
        await asyncio.sleep(1)
        asyncio.get_running_loop().stop()

    def signal_handler():
        if client.is_closed:
            return
        asyncio.create_task(client.drain())
        asyncio.create_task(stop())

    for sig in ("SIGINT", "SIGTERM"):
        asyncio.get_running_loop().add_signal_handler(
            getattr(signal, sig), signal_handler
        )


async def subscribe(stream: str, subject: str, cb: callable, queue: str = None):
    nc = await nats.connect(Config.NATS_URL)
    _handle_signals(nc)

    js = nc.jetstream()
    await js.add_stream(name=stream, subjects=[subject])
    await js.subscribe(subject, cb=cb, stream=stream, queue=queue)


async def publish(subject: str, body: str):
    nc = await nats.connect(Config.NATS_URL)
    js = nc.jetstream()
    await js.publish(subject, body.encode())
    await nc.close()
