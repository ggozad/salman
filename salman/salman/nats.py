import asyncio
import signal

import nats
from nats.js.api import ConsumerConfig, PubAck, StreamInfo
from nats.js.client import JetStreamContext
from nats.js.errors import NotFoundError
from nats.js.kv import KeyValue


class Session:
    def __init__(self, url="nats://localhost:4222"):
        self._done = asyncio.Future()
        self.url = url

    async def __aenter__(self):
        self._nc = await nats.connect(self.url)
        self._js = self._nc.jetstream()
        self._handle_signals()
        return self

    async def __aexit__(self, *args):
        await self.stop()

    async def run_forever(self) -> None:
        try:
            await self._done
        except asyncio.CancelledError:
            await self._nc.close()

    async def stop(self) -> None:
        await self._nc.close()
        if self._done and not self._done.done():
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

    async def add_stream(self, name: str, subjects: list[str]) -> StreamInfo:
        return await self._js.add_stream(name=name, subjects=subjects)

    async def delete_stream(self, name: str) -> bool:
        try:
            return await self._js.delete_stream(name=name)
        except NotFoundError:
            return False

    async def subscribe(
        self,
        stream: str,
        subject: str,
        cb: callable,
        queue: str = None,
        ack_wait: float = None,
    ) -> JetStreamContext.PushSubscription:
        if ack_wait:
            config = ConsumerConfig(ack_wait=ack_wait)
        else:
            config = None
        return await self._js.subscribe(
            subject,
            cb=cb,
            stream=stream,
            queue=queue,
            manual_ack=True,
            config=config,
        )

    async def publish(self, subject: str, data: bytes, stream: str = None) -> PubAck:
        return await self._js.publish(subject, data, stream=stream)

    async def create_kv_bucket(self, name: str) -> KeyValue:
        return await self._js.create_key_value(bucket=name)

    async def delete_kv_bucket(self, bucket: str) -> bool:
        try:
            return await self._js.delete_key_value(bucket=bucket)
        except NotFoundError:
            return False

    async def get_kv_bucket(self, name: str) -> KeyValue:
        return await self._js.create_key_value(bucket=name)
