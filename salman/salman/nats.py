import asyncio
import signal
from typing import List

import nats
from nats.js.api import PubAck, StreamInfo
from nats.js.client import Callback, JetStreamContext
from nats.js.kv import KeyValue


class NATSManager:
    def __init__(self):
        self._nc = None
        self._done = asyncio.Future()

    async def create(self, url="nats://localhost:4222") -> "NATSManager":
        if self._nc is None:
            self._nc = await nats.connect(url)
            self._js = self._nc.jetstream()
            self._handle_signals()
        return self

    async def run_forever(self) -> None:
        await self._done

    async def stop(self) -> None:
        await self._nc.close()
        if self._done:
            self._done.set_result(True)

    def _handle_signals(self) -> None:
        def signal_handler():
            if self._nc.is_closed:
                return
            asyncio.create_task(self.stop())

        for sig in ("SIGINT", "SIGTERM"):
            asyncio.get_running_loop().add_signal_handler(
                getattr(signal, sig), signal_handler
            )

    async def add_stream(self, name: str, subjects: List[str]) -> StreamInfo:
        return await self._js.add_stream(name=name, subjects=subjects)

    async def subscribe(
        self, stream: str, subject: str, cb: Callback, queue: str = None
    ) -> JetStreamContext.PushSubscription:
        return await self._js.subscribe(
            subject, cb=cb, stream=stream, queue=queue, manual_ack=True
        )

    async def publish(self, subject: str, data: bytes, stream: str = None) -> PubAck:
        return await self._js.publish(subject, data, stream=stream)

    async def get_kv_bucket(self, bucket: str) -> KeyValue:
        return await self._js.create_key_value(bucket=bucket)

    async def delete_kv_bucket(self, bucket: str) -> bool:
        return await self._js.delete_key_value(bucket=bucket)
