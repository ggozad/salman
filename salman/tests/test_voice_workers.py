import asyncio

import pytest

from salman.nats import NATSManager
from salman.workers.voice import end_recording, post_blob, recording_handler


@pytest.mark.parametrize("get_test_blobs", ["conversations/1"], indirect=True)
@pytest.mark.asyncio
async def test_voice_detection_worker(get_test_blobs):
    mgr = await NATSManager.create()
    task = asyncio.create_task(recording_handler())

    for i, blob in enumerate(get_test_blobs):
        await post_blob("test", i, get_test_blobs[i])
        await asyncio.sleep(0.1)
    await end_recording("test")

    # await asyncio.sleep(60)

    finished = False

    async def _cb(msg):
        nonlocal finished
        finished = True

    await mgr.subscribe("voice", "segmenting.test.finished", _cb)

    while not finished:
        await asyncio.sleep(0.1)

    task.cancel()
    await mgr.stop()
