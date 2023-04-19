import asyncio
from json import loads

import pytest

from salman.nats import NATSManager
from salman.workers.voice import SUBJECTS, end_recording, post_blob, recording_handler


@pytest.mark.parametrize("get_test_blobs", ["conversations/1"], indirect=True)
@pytest.mark.asyncio
async def test_voice_detection_worker(get_test_blobs):
    mgr = await NATSManager.create()
    await mgr.add_stream("test_stream", SUBJECTS)
    task = asyncio.create_task(recording_handler())

    segments = []

    async def on_segment(msg):
        segments.append(loads(msg.data.decode()))
        await msg.ack()

    async def done(msg):
        nonlocal segments
        task.cancel()
        await mgr.stop()
        assert len(segments) == 14
        assert round(segments[0]["start"], 3) == 0.278
        assert round(segments[0]["end"], 3) == 4.160

    await mgr.subscribe("test_stream", "segments.test.*", on_segment)
    await mgr.subscribe("test_stream", "segmenting.test.finished", done)

    for i, blob in enumerate(get_test_blobs):
        await post_blob("test", i, blob)
        await asyncio.sleep(0.1)
    await end_recording("test")

    await task
